"""Test notification formatting (mocked sending)."""

import pytest

from src.notifications.discord_bot import format_topic_for_discord
from src.notifications.whatsapp import format_topic_for_whatsapp


SAMPLE_TOPIC_DATA = {
    "summary_cn": "学习在德国超市购物时常用的词汇和表达。",
    "vocabulary": [
        {
            "german": "der Einkaufswagen",
            "chinese": "购物车",
            "gender": "der",
            "example_de": "Ich nehme einen Einkaufswagen.",
        },
        {
            "german": "bezahlen",
            "chinese": "付款",
        },
    ],
    "sentences": [
        {
            "german": "Wo finde ich die Milch?",
            "chinese": "牛奶在哪里？",
            "grammar_note": "用于询问位置",
        },
    ],
    "grammar_tips": "名词必须记住冠词。",
    "exercise": "请用德语说：我想买苹果。",
}


def test_format_for_discord() -> None:
    content = format_topic_for_discord(SAMPLE_TOPIC_DATA)
    assert "Einkaufswagen" in content
    assert "购物车" in content
    assert "bezahlen" in content
    assert "核心词汇" in content
    assert "重点句型" in content
    assert "语法提示" in content
    assert "练习" in content


def test_format_for_whatsapp() -> None:
    content = format_topic_for_whatsapp(SAMPLE_TOPIC_DATA)
    assert "Einkaufswagen" in content
    assert "购物车" in content
    assert "核心词汇" in content
    assert "重点句型" in content


def test_format_empty_topic() -> None:
    content = format_topic_for_discord({})
    assert isinstance(content, str)

    content = format_topic_for_whatsapp({})
    assert isinstance(content, str)
