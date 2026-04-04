"""GET /daily-plan — generate a structured 30-60 min daily learning plan."""

import logging
import random
from datetime import date

from fastapi import APIRouter, Depends
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session, get_engine
from src.storage.repository import Repository

logger = logging.getLogger(__name__)

router = APIRouter()


class DailyTask(BaseModel):
    """A single task within the daily plan."""

    order: int
    type: str  # new_topic, vocab_review, sentence_practice, grammar_drill, quiz
    title: str
    title_cn: str
    duration_minutes: int
    data: dict


class DailyPlan(BaseModel):
    """A complete daily learning plan."""

    date: str
    total_minutes: int
    greeting: str
    tasks: list[DailyTask]
    stats: dict


@router.get("/daily-plan", response_model=DailyPlan)
async def get_daily_plan(
    session: AsyncSession = Depends(get_db_session),
) -> DailyPlan:
    """Generate today's 30-60 min structured daily learning plan.

    The plan adapts based on user's learning history:
    - Reviews words user is learning (spaced repetition priority)
    - Introduces a new topic
    - Resurfaces old words that may be forgotten (low review count, old)
    - Includes sentence practice and a quiz
    """
    repo = Repository(session)
    stats = await repo.get_stats()
    today = date.today().isoformat()

    tasks: list[DailyTask] = []
    order = 1
    total_minutes = 0

    # --- Task 1: Vocabulary Review (10 min) ---
    # Review words user is currently learning (status=learning or unknown with reviews)
    review_items = await repo.get_review_vocabulary(count=10)
    review_data = [
        {
            "id": v.id,
            "german": v.german,
            "chinese": v.chinese,
            "gender": v.gender,
            "part_of_speech": v.part_of_speech,
            "example": v.example,
            "status": v.status,
            "review_count": v.review_count,
        }
        for v in review_items
    ]

    if review_data:
        tasks.append(DailyTask(
            order=order,
            type="vocab_review",
            title="Wortschatz wiederholen",
            title_cn="词汇复习",
            duration_minutes=10,
            data={"items": review_data, "instruction_cn": "复习以下词汇，尝试回忆中文含义和用法"},
        ))
        order += 1
        total_minutes += 10

    # --- Task 2: Forgotten Words Resurface (5 min) ---
    # Find words marked known but with low review count — might be forgotten
    forgotten = await repo.get_forgotten_vocabulary(count=5)
    forgotten_data = [
        {
            "id": v.id,
            "german": v.german,
            "chinese": v.chinese,
            "gender": v.gender,
            "example": v.example,
            "review_count": v.review_count,
        }
        for v in forgotten
    ]

    if forgotten_data:
        tasks.append(DailyTask(
            order=order,
            type="forgotten_review",
            title="Vergessene Wörter",
            title_cn="遗忘词汇回顾",
            duration_minutes=5,
            data={
                "items": forgotten_data,
                "instruction_cn": "这些是你之前学过但可能已经遗忘的词汇，请重新复习",
            },
        ))
        order += 1
        total_minutes += 5

    # --- Task 3: New Topic (15 min) ---
    # Generate a fresh topic from a category the user hasn't seen much
    tasks.append(DailyTask(
        order=order,
        type="new_topic",
        title="Neues Thema",
        title_cn="学习新主题",
        duration_minutes=15,
        data={
            "instruction_cn": "今天的新主题将通过AI生成，点击开始学习",
            "action": "generate",
        },
    ))
    order += 1
    total_minutes += 15

    # --- Task 4: Sentence Practice (10 min) ---
    sentences = await repo.list_sentences(status="unknown", limit=5)
    sentence_data = [
        {
            "id": s.id,
            "german": s.german,
            "chinese": s.chinese,
            "grammar_notes": s.grammar_notes,
            "source_topic": s.source_topic,
        }
        for s in sentences
    ]

    if sentence_data:
        tasks.append(DailyTask(
            order=order,
            type="sentence_practice",
            title="Satzübung",
            title_cn="句型练习",
            duration_minutes=10,
            data={
                "items": sentence_data,
                "instruction_cn": "练习以下句型，尝试理解语法结构并造句",
            },
        ))
        order += 1
        total_minutes += 10

    # --- Task 5: Quick Quiz (5 min) ---
    # Mix of known + learning words for a flashcard quiz
    quiz_pool = await repo.get_quiz_vocabulary(count=8)
    quiz_data = []
    for v in quiz_pool:
        quiz_data.append({
            "id": v.id,
            "german": v.german,
            "chinese": v.chinese,
            "gender": v.gender,
        })

    if quiz_data:
        random.shuffle(quiz_data)
        tasks.append(DailyTask(
            order=order,
            type="quiz",
            title="Schnellquiz",
            title_cn="快速测验",
            duration_minutes=5,
            data={
                "items": quiz_data,
                "instruction_cn": "根据德语词汇选择正确的中文含义",
            },
        ))
        order += 1
        total_minutes += 5

    # If no review data at all, bump new topic to 30 min
    if total_minutes < 30:
        for t in tasks:
            if t.type == "new_topic":
                extra = 30 - total_minutes
                t.duration_minutes += extra
                total_minutes = 30
                break

    # Greeting based on stats + level
    from src.heartbeat.curriculum import get_current_module

    total_vocab = stats["vocabulary"]["total"]
    known = stats["vocabulary"]["known"]
    module = get_current_module(total_vocab)

    if total_vocab == 0:
        greeting = "Willkommen! 欢迎开始你的德语学习之旅！今天是第一天，让我们开始吧！"
    elif module is not None:
        greeting = (
            f"Guten Tag! A1·模块{module.id}: {module.name_cn}"
            f" — 已掌握 {total_vocab}/{module.target_vocab} 词汇"
        )
    elif known > 50:
        greeting = f"Sehr gut! 你已经掌握了 {known} 个词汇，继续加油！"
    else:
        greeting = f"Guten Tag! 你的词汇库有 {total_vocab} 个词汇，其中 {known} 个已掌握。今天继续学习吧！"

    return DailyPlan(
        date=today,
        total_minutes=total_minutes,
        greeting=greeting,
        tasks=tasks,
        stats=stats,
    )
