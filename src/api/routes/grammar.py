"""GET /grammar/exercises — generate interactive grammar exercises from user's vocabulary."""

import logging
import random

from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from src.api.dependencies import get_db_session
from src.heartbeat.curriculum import get_current_module
from src.storage.repository import Repository

logger = logging.getLogger(__name__)

router = APIRouter()

# Conjugation tables for common A1 verbs
_REGULAR_CONJUGATIONS = {
    "machen": {"ich": "mache", "du": "machst", "er/sie/es": "macht", "wir": "machen", "ihr": "macht", "sie/Sie": "machen"},
    "spielen": {"ich": "spiele", "du": "spielst", "er/sie/es": "spielt", "wir": "spielen", "ihr": "spielt", "sie/Sie": "spielen"},
    "lernen": {"ich": "lerne", "du": "lernst", "er/sie/es": "lernt", "wir": "lernen", "ihr": "lernt", "sie/Sie": "lernen"},
    "wohnen": {"ich": "wohne", "du": "wohnst", "er/sie/es": "wohnt", "wir": "wohnen", "ihr": "wohnt", "sie/Sie": "wohnen"},
    "kaufen": {"ich": "kaufe", "du": "kaufst", "er/sie/es": "kauft", "wir": "kaufen", "ihr": "kauft", "sie/Sie": "kaufen"},
    "kochen": {"ich": "koche", "du": "kochst", "er/sie/es": "kocht", "wir": "kochen", "ihr": "kocht", "sie/Sie": "kochen"},
    "trinken": {"ich": "trinke", "du": "trinkst", "er/sie/es": "trinkt", "wir": "trinken", "ihr": "trinkt", "sie/Sie": "trinken"},
    "fragen": {"ich": "frage", "du": "fragst", "er/sie/es": "fragt", "wir": "fragen", "ihr": "fragt", "sie/Sie": "fragen"},
    "gehen": {"ich": "gehe", "du": "gehst", "er/sie/es": "geht", "wir": "gehen", "ihr": "geht", "sie/Sie": "gehen"},
    "kommen": {"ich": "komme", "du": "kommst", "er/sie/es": "kommt", "wir": "kommen", "ihr": "kommt", "sie/Sie": "kommen"},
    "heißen": {"ich": "heiße", "du": "heißt", "er/sie/es": "heißt", "wir": "heißen", "ihr": "heißt", "sie/Sie": "heißen"},
    "brauchen": {"ich": "brauche", "du": "brauchst", "er/sie/es": "braucht", "wir": "brauchen", "ihr": "braucht", "sie/Sie": "brauchen"},
    "kosten": {"ich": "koste", "du": "kostest", "er/sie/es": "kostet", "wir": "kosten", "ihr": "kostet", "sie/Sie": "kosten"},
    "arbeiten": {"ich": "arbeite", "du": "arbeitest", "er/sie/es": "arbeitet", "wir": "arbeiten", "ihr": "arbeitet", "sie/Sie": "arbeiten"},
    "zählen": {"ich": "zähle", "du": "zählst", "er/sie/es": "zählt", "wir": "zählen", "ihr": "zählt", "sie/Sie": "zählen"},
}

_IRREGULAR_CONJUGATIONS = {
    "sein": {"ich": "bin", "du": "bist", "er/sie/es": "ist", "wir": "sind", "ihr": "seid", "sie/Sie": "sind"},
    "haben": {"ich": "habe", "du": "hast", "er/sie/es": "hat", "wir": "haben", "ihr": "habt", "sie/Sie": "haben"},
    "fahren": {"ich": "fahre", "du": "fährst", "er/sie/es": "fährt", "wir": "fahren", "ihr": "fahrt", "sie/Sie": "fahren"},
    "sprechen": {"ich": "spreche", "du": "sprichst", "er/sie/es": "spricht", "wir": "sprechen", "ihr": "sprecht", "sie/Sie": "sprechen"},
    "essen": {"ich": "esse", "du": "isst", "er/sie/es": "isst", "wir": "essen", "ihr": "esst", "sie/Sie": "essen"},
    "lesen": {"ich": "lese", "du": "liest", "er/sie/es": "liest", "wir": "lesen", "ihr": "lest", "sie/Sie": "lesen"},
    "schlafen": {"ich": "schlafe", "du": "schläfst", "er/sie/es": "schläft", "wir": "schlafen", "ihr": "schlaft", "sie/Sie": "schlafen"},
    "sehen": {"ich": "sehe", "du": "siehst", "er/sie/es": "sieht", "wir": "sehen", "ihr": "seht", "sie/Sie": "sehen"},
    "nehmen": {"ich": "nehme", "du": "nimmst", "er/sie/es": "nimmt", "wir": "nehmen", "ihr": "nehmt", "sie/Sie": "nehmen"},
    "möchten": {"ich": "möchte", "du": "möchtest", "er/sie/es": "möchte", "wir": "möchten", "ihr": "möchtet", "sie/Sie": "möchten"},
    "können": {"ich": "kann", "du": "kannst", "er/sie/es": "kann", "wir": "können", "ihr": "könnt", "sie/Sie": "können"},
    "müssen": {"ich": "muss", "du": "musst", "er/sie/es": "muss", "wir": "müssen", "ihr": "müsst", "sie/Sie": "müssen"},
    "wollen": {"ich": "will", "du": "willst", "er/sie/es": "will", "wir": "wollen", "ihr": "wollt", "sie/Sie": "wollen"},
}

# Cloze sentence templates per module
_CLOZE_TEMPLATES = {
    1: [
        {"sentence": "Ich ___ Maria.", "answer": "heiße", "options": ["heiße", "heißt", "heißen", "bin"], "hint_cn": "我叫Maria。", "grammar_cn": "heißen的ich变位：heiße"},
        {"sentence": "Wie ___ du?", "answer": "heißt", "options": ["heißt", "heiße", "heißen", "ist"], "hint_cn": "你叫什么？", "grammar_cn": "heißen的du变位：heißt"},
        {"sentence": "Ich ___ aus China.", "answer": "komme", "options": ["komme", "kommst", "kommt", "kommen"], "hint_cn": "我来自中国。", "grammar_cn": "kommen的ich变位：komme"},
        {"sentence": "Er ___ Student.", "answer": "ist", "options": ["ist", "bin", "bist", "sind"], "hint_cn": "他是学生。", "grammar_cn": "sein的er变位：ist"},
        {"sentence": "Wir ___ Deutsch.", "answer": "lernen", "options": ["lernen", "lerne", "lernst", "lernt"], "hint_cn": "我们学德语。", "grammar_cn": "lernen的wir变位：lernen"},
        {"sentence": "___ geht es Ihnen?", "answer": "Wie", "options": ["Wie", "Was", "Wo", "Wer"], "hint_cn": "您好吗？", "grammar_cn": "wie用来询问状态/方式"},
    ],
    2: [
        {"sentence": "Es ___ drei Uhr.", "answer": "ist", "options": ["ist", "bin", "bist", "hat"], "hint_cn": "现在三点钟。", "grammar_cn": "表达时间用 es ist + 时间"},
        {"sentence": "Ich ___ um 7 Uhr auf.", "answer": "stehe", "options": ["stehe", "stehst", "steht", "stehen"], "hint_cn": "我七点起床。", "grammar_cn": "aufstehen可分动词：ich stehe...auf"},
        {"sentence": "Wann ___ du?", "answer": "kommst", "options": ["kommst", "komme", "kommt", "kommen"], "hint_cn": "你什么时候来？", "grammar_cn": "kommen的du变位：kommst"},
        {"sentence": "Das ___ fünf Euro.", "answer": "kostet", "options": ["kostet", "koste", "kostest", "kosten"], "hint_cn": "这个五欧元。", "grammar_cn": "kosten的第三人称：kostet"},
        {"sentence": "___ viel kostet das?", "answer": "Wie", "options": ["Wie", "Was", "Wo", "Wann"], "hint_cn": "这个多少钱？", "grammar_cn": "wie viel询问数量或价格"},
    ],
    3: [
        {"sentence": "Ich ___ zwei Brüder.", "answer": "habe", "options": ["habe", "hast", "hat", "haben"], "hint_cn": "我有两个兄弟。", "grammar_cn": "haben的ich变位：habe"},
        {"sentence": "Er ___ gern Fußball.", "answer": "spielt", "options": ["spielt", "spiele", "spielst", "spielen"], "hint_cn": "他喜欢踢足球。", "grammar_cn": "spielen的er变位：spielt"},
        {"sentence": "Wir gehen ___ Kino.", "answer": "ins", "options": ["ins", "in", "im", "an"], "hint_cn": "我们去电影院。", "grammar_cn": "ins = in das（去某个地方）"},
        {"sentence": "Ich spiele ___ gern Tennis.", "answer": "nicht", "options": ["nicht", "kein", "nein", "keine"], "hint_cn": "我不喜欢打网球。", "grammar_cn": "nicht否定动词，kein否定名词"},
        {"sentence": "Hast du ___ Hobby?", "answer": "ein", "options": ["ein", "eine", "einen", "einer"], "hint_cn": "你有爱好吗？", "grammar_cn": "Hobby是中性名词（das Hobby），不定冠词：ein"},
    ],
    4: [
        {"sentence": "Ich kaufe ___ Apfel.", "answer": "einen", "options": ["einen", "ein", "eine", "der"], "hint_cn": "我买一个苹果。", "grammar_cn": "Akkusativ阳性：ein→einen"},
        {"sentence": "Ich möchte ___ Kaffee.", "answer": "einen", "options": ["einen", "ein", "eine", "der"], "hint_cn": "我想要一杯咖啡。", "grammar_cn": "Akkusativ阳性：ein→einen"},
        {"sentence": "Wo ___ der Bahnhof?", "answer": "ist", "options": ["ist", "bin", "bist", "sind"], "hint_cn": "火车站在哪？", "grammar_cn": "用wo + sein询问地点"},
        {"sentence": "Gehen Sie ___.", "answer": "geradeaus", "options": ["geradeaus", "rechts", "links", "zurück"], "hint_cn": "请直走。", "grammar_cn": "geradeaus = 直走"},
        {"sentence": "Ich hätte ___ eine Suppe.", "answer": "gern", "options": ["gern", "gut", "viel", "sehr"], "hint_cn": "我想要一碗汤。", "grammar_cn": "Ich hätte gern = 我想要（点餐礼貌用语）"},
    ],
    5: [
        {"sentence": "Die Wohnung ___ drei Zimmer.", "answer": "hat", "options": ["hat", "habe", "hast", "ist"], "hint_cn": "这套公寓有三个房间。", "grammar_cn": "haben的第三人称：hat"},
        {"sentence": "Ich fahre ___ dem Bus.", "answer": "mit", "options": ["mit", "in", "auf", "an"], "hint_cn": "我坐公交车。", "grammar_cn": "mit + Dativ 表示使用交通工具"},
        {"sentence": "Ich ___ nach Berlin fahren.", "answer": "muss", "options": ["muss", "musst", "müssen", "kann"], "hint_cn": "我必须去柏林。", "grammar_cn": "müssen的ich变位：muss"},
        {"sentence": "Der Stuhl steht ___ der Küche.", "answer": "in", "options": ["in", "auf", "an", "mit"], "hint_cn": "椅子在厨房里。", "grammar_cn": "in + Dativ 表示在...里面"},
    ],
    6: [
        {"sentence": "Mir tut ___ Kopf weh.", "answer": "der", "options": ["der", "die", "das", "den"], "hint_cn": "我头疼。", "grammar_cn": "Kopf是阳性名词（der Kopf）"},
        {"sentence": "Ich ___ Fieber.", "answer": "habe", "options": ["habe", "bin", "hast", "hat"], "hint_cn": "我发烧了。", "grammar_cn": "haben表示'患有'某种症状"},
        {"sentence": "Es ___ heute.", "answer": "regnet", "options": ["regnet", "regnt", "regen", "regent"], "hint_cn": "今天下雨。", "grammar_cn": "regnen的第三人称：es regnet"},
        {"sentence": "Im Winter ist es ___.", "answer": "kalt", "options": ["kalt", "heiß", "warm", "kühl"], "hint_cn": "冬天很冷。", "grammar_cn": "im Winter = 在冬天"},
    ],
}

_PRONOUNS = ["ich", "du", "er/sie/es", "wir", "ihr", "sie/Sie"]


def _build_article_exercises(nouns: list[dict], count: int = 8) -> list[dict]:
    """Build der/die/das article selection exercises from user's vocabulary."""
    noun_items = [v for v in nouns if v.get("gender") and v["gender"] in ("der", "die", "das")]
    if not noun_items:
        return []

    random.shuffle(noun_items)
    exercises = []
    for v in noun_items[:count]:
        exercises.append({
            "type": "article",
            "german": v["german"],
            "chinese": v["chinese"],
            "correct": v["gender"],
            "options": ["der", "die", "das"],
        })
    return exercises


def _build_cloze_exercises(module_id: int, count: int = 5) -> list[dict]:
    """Build fill-in-the-blank exercises for the current module."""
    templates = _CLOZE_TEMPLATES.get(module_id, [])
    if not templates:
        # Gather from all modules up to current
        for m in range(1, module_id + 1):
            templates.extend(_CLOZE_TEMPLATES.get(m, []))
    if not templates:
        return []

    random.shuffle(templates)
    exercises = []
    for t in templates[:count]:
        opts = list(t["options"])
        random.shuffle(opts)
        exercises.append({
            "type": "cloze",
            "sentence": t["sentence"],
            "correct": t["answer"],
            "options": opts,
            "hint_cn": t["hint_cn"],
            "grammar_cn": t["grammar_cn"],
        })
    return exercises


def _build_conjugation_exercises(module_id: int, count: int = 4) -> list[dict]:
    """Build verb conjugation exercises."""
    # Pick verbs based on module
    if module_id <= 2:
        pool = {k: v for k, v in _IRREGULAR_CONJUGATIONS.items() if k in ("sein", "haben")}
        pool.update({k: v for k, v in _REGULAR_CONJUGATIONS.items() if k in ("machen", "lernen", "spielen", "kommen", "heißen")})
    elif module_id <= 4:
        pool = dict(_IRREGULAR_CONJUGATIONS)
        pool.update(dict(list(_REGULAR_CONJUGATIONS.items())[:8]))
    else:
        pool = dict(_IRREGULAR_CONJUGATIONS)
        pool.update(_REGULAR_CONJUGATIONS)

    verbs = list(pool.items())
    random.shuffle(verbs)
    exercises = []

    for verb, table in verbs[:count]:
        # Pick 2-3 pronouns to fill in, reveal the rest
        pronouns = list(table.keys())
        random.shuffle(pronouns)
        blanks = pronouns[:random.randint(2, 3)]

        cells = []
        for p in _PRONOUNS:
            cells.append({
                "pronoun": p,
                "answer": table[p],
                "is_blank": p in blanks,
            })

        # Build wrong options from other forms for distractors
        all_forms = list(set(table.values()))
        exercises.append({
            "type": "conjugation",
            "verb": verb,
            "cells": cells,
            "all_forms": all_forms,
        })

    return exercises


def _build_sentence_order_exercises(module_id: int, count: int = 3) -> list[dict]:
    """Build sentence word-order exercises."""
    templates = {
        1: [
            {"words": ["Ich", "heiße", "Anna", "."], "correct": "Ich heiße Anna.", "hint_cn": "我叫Anna。"},
            {"words": ["Er", "ist", "Student", "."], "correct": "Er ist Student.", "hint_cn": "他是学生。"},
            {"words": ["Wie", "heißt", "du", "?"], "correct": "Wie heißt du?", "hint_cn": "你叫什么？"},
            {"words": ["Ich", "komme", "aus", "China", "."], "correct": "Ich komme aus China.", "hint_cn": "我来自中国。"},
        ],
        2: [
            {"words": ["Es", "ist", "drei", "Uhr", "."], "correct": "Es ist drei Uhr.", "hint_cn": "现在三点。"},
            {"words": ["Ich", "stehe", "um", "7 Uhr", "auf", "."], "correct": "Ich stehe um 7 Uhr auf.", "hint_cn": "我七点起床。"},
            {"words": ["Das", "kostet", "fünf", "Euro", "."], "correct": "Das kostet fünf Euro.", "hint_cn": "这个五欧元。"},
        ],
        3: [
            {"words": ["Ich", "habe", "eine", "Schwester", "."], "correct": "Ich habe eine Schwester.", "hint_cn": "我有一个姐妹。"},
            {"words": ["Er", "spielt", "gern", "Fußball", "."], "correct": "Er spielt gern Fußball.", "hint_cn": "他喜欢踢足球。"},
            {"words": ["Wir", "gehen", "ins", "Kino", "."], "correct": "Wir gehen ins Kino.", "hint_cn": "我们去电影院。"},
        ],
        4: [
            {"words": ["Ich", "kaufe", "einen", "Apfel", "."], "correct": "Ich kaufe einen Apfel.", "hint_cn": "我买一个苹果。"},
            {"words": ["Wo", "ist", "der", "Bahnhof", "?"], "correct": "Wo ist der Bahnhof?", "hint_cn": "火车站在哪？"},
            {"words": ["Ich", "möchte", "einen", "Kaffee", "."], "correct": "Ich möchte einen Kaffee.", "hint_cn": "我想要一杯咖啡。"},
        ],
        5: [
            {"words": ["Ich", "fahre", "mit", "dem", "Bus", "."], "correct": "Ich fahre mit dem Bus.", "hint_cn": "我坐公交车。"},
            {"words": ["Die", "Wohnung", "hat", "drei", "Zimmer", "."], "correct": "Die Wohnung hat drei Zimmer.", "hint_cn": "这套公寓有三个房间。"},
        ],
        6: [
            {"words": ["Es", "regnet", "heute", "."], "correct": "Es regnet heute.", "hint_cn": "今天下雨。"},
            {"words": ["Ich", "habe", "Fieber", "."], "correct": "Ich habe Fieber.", "hint_cn": "我发烧了。"},
        ],
    }

    pool = []
    for m in range(1, module_id + 1):
        pool.extend(templates.get(m, []))
    if not pool:
        return []

    random.shuffle(pool)
    exercises = []
    for t in pool[:count]:
        shuffled = list(t["words"])
        # Keep shuffling until order is different
        for _ in range(10):
            random.shuffle(shuffled)
            if shuffled != t["words"]:
                break
        exercises.append({
            "type": "sentence_order",
            "words": shuffled,
            "correct": t["correct"],
            "hint_cn": t["hint_cn"],
        })
    return exercises


@router.get("/grammar/exercises")
async def get_grammar_exercises(
    session: AsyncSession = Depends(get_db_session),
) -> dict:
    """Generate a set of grammar exercises based on current level and vocabulary."""
    repo = Repository(session)
    vocab_count = await repo.count_vocabulary()
    module = get_current_module(vocab_count)
    module_id = module.id if module else 6

    # Get user's nouns for article exercises
    all_vocab = await repo.list_vocabulary(limit=500)
    vocab_dicts = [
        {
            "german": v.german,
            "chinese": v.chinese,
            "gender": v.gender,
            "part_of_speech": v.part_of_speech,
        }
        for v in all_vocab
    ]

    exercises = []
    exercises.extend(_build_article_exercises(vocab_dicts, count=6))
    exercises.extend(_build_cloze_exercises(module_id, count=5))
    exercises.extend(_build_conjugation_exercises(module_id, count=3))
    exercises.extend(_build_sentence_order_exercises(module_id, count=3))

    random.shuffle(exercises)

    return {
        "module_id": module_id,
        "module_name_cn": module.name_cn if module else "综合练习",
        "level": "A1",
        "total": len(exercises),
        "exercises": exercises,
    }
