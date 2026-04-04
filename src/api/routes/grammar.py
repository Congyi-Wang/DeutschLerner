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

# Grammar lessons per module — displayed before exercises
_GRAMMAR_LESSONS: dict[int, list[dict]] = {
    1: [
        {
            "title": "sein \u52a8\u8bcd\u53d8\u4f4d",
            "explanation_cn": (
                "sein\uff08\u662f\uff09\u662f\u5fb7\u8bed\u6700\u91cd\u8981\u7684\u52a8\u8bcd\u4e4b\u4e00\uff0c"
                "\u76f8\u5f53\u4e8e\u82f1\u8bed\u7684 be\u3002\u5b83\u662f\u4e0d\u89c4\u5219\u52a8\u8bcd\uff0c"
                "\u6bcf\u4e2a\u4eba\u79f0\u7684\u53d8\u4f4d\u5f62\u5f0f\u90fd\u4e0d\u540c\uff0c\u5fc5\u987b\u9010\u4e00\u8bb0\u5fc6\u3002"
            ),
            "examples": [
                {"de": "Ich bin Student.", "cn": "\u6211\u662f\u5b66\u751f\u3002"},
                {"de": "Du bist nett.", "cn": "\u4f60\u5f88\u53cb\u597d\u3002"},
                {"de": "Er ist aus Deutschland.", "cn": "\u4ed6\u6765\u81ea\u5fb7\u56fd\u3002"},
            ],
            "table": {
                "ich": "bin", "du": "bist", "er/sie/es": "ist",
                "wir": "sind", "ihr": "seid", "sie/Sie": "sind",
            },
            "tip_cn": "\u8bb0\u5fc6\u53e3\u8bc0\uff1a\u6211bin\u4f60bist\u4ed6ist\uff0c\u6211\u4eec sind\u4f60\u4eecseid\u4ed6\u4eecsind\u3002",
        },
        {
            "title": "\u4eba\u79f0\u4ee3\u8bcd",
            "explanation_cn": (
                "\u5fb7\u8bed\u7684\u4eba\u79f0\u4ee3\u8bcd\u5206\u4e3a\u7b2c\u4e00\u3001\u4e8c\u3001\u4e09\u4eba\u79f0\uff0c"
                "\u5355\u590d\u6570\u5404\u6709\u4e0d\u540c\u5f62\u5f0f\u3002"
                "Sie\uff08\u5927\u5199\uff09\u662f\u5c0a\u79f0\u300c\u60a8\u300d\uff0c\u7528\u4e8e\u6b63\u5f0f\u573a\u5408\u3002"
            ),
            "examples": [
                {"de": "Ich hei\u00dfe Anna.", "cn": "\u6211\u53ebAnna\u3002"},
                {"de": "Woher kommst du?", "cn": "\u4f60\u4ece\u54ea\u91cc\u6765\uff1f"},
                {"de": "Sie ist Lehrerin.", "cn": "\u5979\u662f\u8001\u5e08\u3002"},
            ],
            "table": None,
            "tip_cn": "\u6ce8\u610f\uff1asie \u5c0f\u5199\u53ef\u4ee5\u662f\u300c\u5979\u300d\u6216\u300c\u4ed6\u4eec\u300d\uff0cSie \u5927\u5199\u662f\u300c\u60a8\u300d\u3002",
        },
        {
            "title": "\u57fa\u672c\u8bed\u5e8f SVO",
            "explanation_cn": (
                "\u5fb7\u8bed\u9648\u8ff0\u53e5\u7684\u57fa\u672c\u8bed\u5e8f\u662f\u4e3b\u8bed + \u52a8\u8bcd + \u5176\u4ed6\u6210\u5206\uff08SVO\uff09\u3002"
                "\u52a8\u8bcd\u59cb\u7ec8\u5728\u7b2c\u4e8c\u4f4d\uff0c\u8fd9\u662f\u5fb7\u8bed\u8bed\u5e8f\u7684\u6838\u5fc3\u89c4\u5219\u3002"
            ),
            "examples": [
                {"de": "Ich komme aus China.", "cn": "\u6211\u6765\u81ea\u4e2d\u56fd\u3002"},
                {"de": "Er lernt Deutsch.", "cn": "\u4ed6\u5b66\u5fb7\u8bed\u3002"},
                {"de": "Wie hei\u00dft du?", "cn": "\u4f60\u53eb\u4ec0\u4e48\uff1f\uff08\u7591\u95ee\u8bcd\u5360\u7b2c\u4e00\u4f4d\uff0c\u52a8\u8bcd\u4ecd\u5728\u7b2c\u4e8c\u4f4d\uff09"},
            ],
            "table": None,
            "tip_cn": "\u8bb0\u4f4f\u300c\u52a8\u8bcd\u7b2c\u4e8c\u4f4d\u300d\u539f\u5219\uff1a\u4e0d\u7ba1\u53e5\u9996\u662f\u4ec0\u4e48\uff0c\u52a8\u8bcd\u6c38\u8fdc\u6392\u7b2c\u4e8c\u3002",
        },
    ],
    2: [
        {
            "title": "\u89c4\u5219\u52a8\u8bcd\u53d8\u4f4d",
            "explanation_cn": (
                "\u5fb7\u8bed\u89c4\u5219\u52a8\u8bcd\u7684\u53d8\u4f4d\u9075\u5faa\u56fa\u5b9a\u6a21\u5f0f\uff1a"
                "\u53bb\u6389\u8bcd\u5c3e -en \u5f97\u5230\u8bcd\u5e72\uff0c\u518d\u52a0\u4e0a\u4eba\u79f0\u8bcd\u5c3e "
                "-e/-st/-t/-en/-t/-en\u3002\u5927\u591a\u6570\u52a8\u8bcd\u90fd\u9075\u5faa\u8fd9\u4e2a\u89c4\u5f8b\u3002"
            ),
            "examples": [
                {"de": "Ich mache Sport.", "cn": "\u6211\u505a\u8fd0\u52a8\u3002"},
                {"de": "Du spielst Gitarre.", "cn": "\u4f60\u5f39\u5409\u4ed6\u3002"},
                {"de": "Er lernt Deutsch.", "cn": "\u4ed6\u5b66\u5fb7\u8bed\u3002"},
            ],
            "table": {
                "ich": "-e", "du": "-st", "er/sie/es": "-t",
                "wir": "-en", "ihr": "-t", "sie/Sie": "-en",
            },
            "tip_cn": "\u8bcd\u5e72 + \u8bcd\u5c3e\uff1amach+e, mach+st, mach+t, mach+en, mach+t, mach+en\u3002",
        },
        {
            "title": "\u65f6\u95f4\u8868\u8fbe um + Uhr",
            "explanation_cn": (
                "\u8868\u8fbe\u6574\u70b9\u65f6\u95f4\u7528 es ist + \u6570\u5b57 + Uhr\u3002"
                "\u8868\u793a\u300c\u5728\u51e0\u70b9\u300d\u7528\u4ecb\u8bcd um\u3002"
                "\u5fb7\u8bed\u65e5\u5e38\u752812\u5c0f\u65f6\u5236\uff0c\u6b63\u5f0f\u573a\u5408\u752824\u5c0f\u65f6\u5236\u3002"
            ),
            "examples": [
                {"de": "Es ist drei Uhr.", "cn": "\u73b0\u5728\u4e09\u70b9\u949f\u3002"},
                {"de": "Ich stehe um 7 Uhr auf.", "cn": "\u6211\u4e03\u70b9\u8d77\u5e8a\u3002"},
                {"de": "Um wie viel Uhr kommst du?", "cn": "\u4f60\u51e0\u70b9\u6765\uff1f"},
            ],
            "table": None,
            "tip_cn": "um \u662f\u300c\u5728\uff08\u51e0\u70b9\uff09\u300d\u7684\u610f\u601d\uff0cUhr \u662f\u300c\u70b9\u949f\u300d\uff0c\u4e24\u8005\u642d\u914d\u4f7f\u7528\u3002",
        },
        {
            "title": "W-\u7591\u95ee\u8bcd",
            "explanation_cn": (
                "\u5fb7\u8bed\u7684\u7279\u6b8a\u7591\u95ee\u53e5\u4ee5W-\u7591\u95ee\u8bcd\u5f00\u5934\uff0c"
                "\u52a8\u8bcd\u7d27\u8ddf\u5176\u540e\u653e\u5728\u7b2c\u4e8c\u4f4d\u3002"
                "\u5e38\u7528\u7591\u95ee\u8bcd\uff1awann\uff08\u4f55\u65f6\uff09\u3001wie viel\uff08\u591a\u5c11\uff09\u3001was\uff08\u4ec0\u4e48\uff09\u3001wo\uff08\u54ea\u91cc\uff09\u3002"
            ),
            "examples": [
                {"de": "Wann kommst du?", "cn": "\u4f60\u4ec0\u4e48\u65f6\u5019\u6765\uff1f"},
                {"de": "Wie viel kostet das?", "cn": "\u8fd9\u4e2a\u591a\u5c11\u94b1\uff1f"},
                {"de": "Was machst du?", "cn": "\u4f60\u5728\u505a\u4ec0\u4e48\uff1f"},
            ],
            "table": None,
            "tip_cn": "\u6240\u6709W-\u7591\u95ee\u8bcd\u90fd\u4ee5W\u5f00\u5934\uff0c\u8bed\u5e8f\uff1aW-\u8bcd + \u52a8\u8bcd + \u4e3b\u8bed + \u5176\u4ed6\u3002",
        },
    ],
    3: [
        {
            "title": "haben \u52a8\u8bcd\u53d8\u4f4d",
            "explanation_cn": (
                "haben\uff08\u6709\uff09\u662f\u5fb7\u8bed\u7b2c\u4e8c\u5927\u91cd\u8981\u52a8\u8bcd\u3002"
                "\u5b83\u4e5f\u662f\u4e0d\u89c4\u5219\u52a8\u8bcd\uff0cdu \u548c er/sie/es \u5f62\u5f0f\u9700\u8981\u7279\u522b\u6ce8\u610f\u3002"
                "haben \u4e5f\u662f\u6784\u6210\u5b8c\u6210\u65f6\u7684\u52a9\u52a8\u8bcd\u3002"
            ),
            "examples": [
                {"de": "Ich habe zwei Br\u00fcder.", "cn": "\u6211\u6709\u4e24\u4e2a\u5144\u5f1f\u3002"},
                {"de": "Hast du Zeit?", "cn": "\u4f60\u6709\u65f6\u95f4\u5417\uff1f"},
                {"de": "Er hat ein Auto.", "cn": "\u4ed6\u6709\u4e00\u8f86\u8f66\u3002"},
            ],
            "table": {
                "ich": "habe", "du": "hast", "er/sie/es": "hat",
                "wir": "haben", "ihr": "habt", "sie/Sie": "haben",
            },
            "tip_cn": "\u6ce8\u610f du hast \u548c er hat \u7684\u7279\u6b8a\u5f62\u5f0f\uff0c\u5176\u4ed6\u4eba\u79f0\u90fd\u662f\u89c4\u5219\u7684\u3002",
        },
        {
            "title": "nicht \u4e0e kein \u5426\u5b9a",
            "explanation_cn": (
                "\u5fb7\u8bed\u6709\u4e24\u79cd\u5426\u5b9a\u65b9\u5f0f\uff1a"
                "nicht \u5426\u5b9a\u52a8\u8bcd\u3001\u5f62\u5bb9\u8bcd\u548c\u526f\u8bcd\uff1b"
                "kein \u5426\u5b9a\u5e26\u4e0d\u5b9a\u51a0\u8bcd\u7684\u540d\u8bcd\uff08\u76f8\u5f53\u4e8e nicht ein\uff09\u3002"
                "\u6ca1\u6709\u51a0\u8bcd\u7684\u540d\u8bcd\u4e5f\u7528 kein\u3002"
            ),
            "examples": [
                {"de": "Ich spiele nicht gern Tennis.", "cn": "\u6211\u4e0d\u559c\u6b22\u6253\u7f51\u7403\u3002\uff08\u5426\u5b9a\u52a8\u8bcd\uff09"},
                {"de": "Ich habe kein Auto.", "cn": "\u6211\u6ca1\u6709\u8f66\u3002\uff08\u5426\u5b9a\u540d\u8bcd\uff09"},
                {"de": "Das ist keine Katze.", "cn": "\u90a3\u4e0d\u662f\u732b\u3002\uff08\u5426\u5b9a\u540d\u8bcd\uff09"},
            ],
            "table": None,
            "tip_cn": "\u7b80\u5355\u8bb0\uff1a\u5426\u5b9a\u540d\u8bcd\u7528 kein\uff0c\u5426\u5b9a\u5176\u4ed6\u7528 nicht\u3002",
        },
        {
            "title": "gern / nicht gern \u8868\u8fbe\u559c\u597d",
            "explanation_cn": (
                "\u5728\u52a8\u8bcd\u540e\u52a0 gern \u8868\u793a\u559c\u6b22\u505a\u67d0\u4e8b\uff0c"
                "\u52a0 nicht gern \u8868\u793a\u4e0d\u559c\u6b22\u3002"
                "gern \u653e\u5728\u52a8\u8bcd\u4e4b\u540e\u3001\u5bbe\u8bed\u4e4b\u524d\u3002"
            ),
            "examples": [
                {"de": "Ich spiele gern Fu\u00dfball.", "cn": "\u6211\u559c\u6b22\u8e22\u8db3\u7403\u3002"},
                {"de": "Er kocht nicht gern.", "cn": "\u4ed6\u4e0d\u559c\u6b22\u505a\u996d\u3002"},
                {"de": "Spielst du gern Gitarre?", "cn": "\u4f60\u559c\u6b22\u5f39\u5409\u4ed6\u5417\uff1f"},
            ],
            "table": None,
            "tip_cn": "gern \u662f\u526f\u8bcd\uff0c\u76f4\u63a5\u653e\u5728\u52a8\u8bcd\u540e\u9762\uff0c\u4e0d\u9700\u8981\u989d\u5916\u7684\u52a8\u8bcd\u3002",
        },
    ],
    4: [
        {
            "title": "\u51a0\u8bcd\u7cfb\u7edf der/die/das",
            "explanation_cn": (
                "\u5fb7\u8bed\u540d\u8bcd\u5206\u9633\u6027(der)\u3001\u9634\u6027(die)\u3001\u4e2d\u6027(das)\u4e09\u79cd\u6027\u522b\u3002"
                "\u540d\u8bcd\u7684\u6027\u522b\u5fc5\u987b\u548c\u51a0\u8bcd\u4e00\u8d77\u8bb0\u5fc6\uff0c"
                "\u56e0\u4e3a\u6ca1\u6709\u5b8c\u5168\u53ef\u9760\u7684\u89c4\u5219\u3002\u4e0d\u8fc7\u6709\u4e00\u4e9b\u89c4\u5f8b\u53ef\u4ee5\u5e2e\u52a9\u5224\u65ad\u3002"
            ),
            "examples": [
                {"de": "der Mann, der Apfel", "cn": "\u7537\u4eba\u3001\u82f9\u679c\uff08\u9633\u6027\uff09"},
                {"de": "die Frau, die Milch", "cn": "\u5973\u4eba\u3001\u725b\u5976\uff08\u9634\u6027\uff09"},
                {"de": "das Kind, das Buch", "cn": "\u5b69\u5b50\u3001\u4e66\uff08\u4e2d\u6027\uff09"},
            ],
            "table": None,
            "tip_cn": "\u5c0f\u7a8d\u95e8\uff1a-ung/-heit/-keit \u7ed3\u5c3e\u591a\u4e3a\u9634\u6027\uff0c-chen/-lein \u7ed3\u5c3e\u4e3a\u4e2d\u6027\u3002",
        },
        {
            "title": "\u7b2c\u56db\u683c Akkusativ",
            "explanation_cn": (
                "\u5f53\u540d\u8bcd\u505a\u76f4\u63a5\u5bbe\u8bed\u65f6\u8981\u7528\u7b2c\u56db\u683c\uff08Akkusativ\uff09\u3002"
                "\u53ea\u6709\u9633\u6027\u540d\u8bcd\u7684\u51a0\u8bcd\u4f1a\u53d8\u5316\uff1ader\u2192den\uff0cein\u2192einen\u3002"
                "\u9634\u6027\u3001\u4e2d\u6027\u548c\u590d\u6570\u4e0d\u53d8\u3002"
            ),
            "examples": [
                {"de": "Ich kaufe einen Apfel.", "cn": "\u6211\u4e70\u4e00\u4e2a\u82f9\u679c\u3002\uff08ein\u2192einen\uff09"},
                {"de": "Ich trinke eine Milch.", "cn": "\u6211\u559d\u725b\u5976\u3002\uff08eine \u4e0d\u53d8\uff09"},
                {"de": "Ich sehe das Kind.", "cn": "\u6211\u770b\u89c1\u90a3\u4e2a\u5b69\u5b50\u3002\uff08das \u4e0d\u53d8\uff09"},
            ],
            "table": {
                "\u9633\u6027 der": "den", "\u9634\u6027 die": "die",
                "\u4e2d\u6027 das": "das", "\u590d\u6570 die": "die",
            },
            "tip_cn": "\u53ea\u6709\u9633\u6027\u4f1a\u53d8\uff01der\u2192den, ein\u2192einen\uff0c\u5176\u4ed6\u683c\u4e0d\u53d8\u3002",
        },
        {
            "title": "m\u00f6chten \u7528\u6cd5",
            "explanation_cn": (
                "m\u00f6chten\uff08\u60f3\u8981\uff09\u662f\u70b9\u9910\u548c\u8868\u8fbe\u613f\u671b\u7684\u5e38\u7528\u52a8\u8bcd\uff0c"
                "\u8bed\u6c14\u6bd4 wollen \u66f4\u793c\u8c8c\u3002"
                "\u5b83\u662f\u60c5\u6001\u52a8\u8bcd m\u00f6gen \u7684\u865a\u62df\u5f0f\uff0c\u540e\u63a5\u52a8\u8bcd\u539f\u5f62\u6216\u76f4\u63a5\u63a5\u540d\u8bcd\u3002"
            ),
            "examples": [
                {"de": "Ich m\u00f6chte einen Kaffee.", "cn": "\u6211\u60f3\u8981\u4e00\u676f\u5496\u5561\u3002"},
                {"de": "Ich m\u00f6chte bestellen.", "cn": "\u6211\u60f3\u70b9\u9910\u3002"},
                {"de": "M\u00f6chtest du Tee?", "cn": "\u4f60\u60f3\u8981\u8336\u5417\uff1f"},
            ],
            "table": {
                "ich": "m\u00f6chte", "du": "m\u00f6chtest", "er/sie/es": "m\u00f6chte",
                "wir": "m\u00f6chten", "ihr": "m\u00f6chtet", "sie/Sie": "m\u00f6chten",
            },
            "tip_cn": "\u70b9\u9910\u4e07\u80fd\u53e5\u578b\uff1aIch m\u00f6chte + \u98df\u7269/\u996e\u6599\uff08\u7b2c\u56db\u683c\uff09\u3002",
        },
    ],
    5: [
        {
            "title": "\u4ecb\u8bcd in/auf/an/nach/zu",
            "explanation_cn": (
                "\u5fb7\u8bed\u65b9\u4f4d\u4ecb\u8bcd\u7528\u6cd5\u5404\u4e0d\u540c\uff1a"
                "in\uff08\u5728\u2026\u91cc\u9762\uff09\u3001auf\uff08\u5728\u2026\u4e0a\u9762\uff09\u3001"
                "an\uff08\u5728\u2026\u65c1\u8fb9/\u9760\u7740\uff09\u3001"
                "nach\uff08\u53bb\u67d0\u5730/\u57ce\u5e02/\u56fd\u5bb6\uff09\u3001"
                "zu\uff08\u53bb\u67d0\u4eba\u90a3\u91cc/\u53bb\u67d0\u673a\u6784\uff09\u3002"
            ),
            "examples": [
                {"de": "Ich bin in der K\u00fcche.", "cn": "\u6211\u5728\u53a8\u623f\u91cc\u3002"},
                {"de": "Das Buch liegt auf dem Tisch.", "cn": "\u4e66\u5728\u684c\u5b50\u4e0a\u3002"},
                {"de": "Ich fahre nach Berlin.", "cn": "\u6211\u53bb\u67cf\u6797\u3002"},
                {"de": "Ich gehe zum Arzt.", "cn": "\u6211\u53bb\u770b\u533b\u751f\u3002"},
            ],
            "table": None,
            "tip_cn": "\u53bb\u57ce\u5e02/\u56fd\u5bb6\u7528 nach\uff0c\u53bb\u4eba/\u673a\u6784\u7528 zu\uff0c\u5728\u91cc\u9762\u7528 in\u3002",
        },
        {
            "title": "\u7b2c\u4e09\u683c Dativ \u57fa\u7840",
            "explanation_cn": (
                "\u67d0\u4e9b\u4ecb\u8bcd\uff08\u5982 mit, in, auf, an \u8868\u9759\u6001\u4f4d\u7f6e\u65f6\uff09"
                "\u8981\u6c42\u540d\u8bcd\u7528\u7b2c\u4e09\u683c Dativ\u3002"
                "\u7b2c\u4e09\u683c\u7684\u51a0\u8bcd\u53d8\u5316\uff1ader\u2192dem, die\u2192der, das\u2192dem\u3002"
            ),
            "examples": [
                {"de": "Ich fahre mit dem Bus.", "cn": "\u6211\u5750\u516c\u4ea4\u8f66\u3002\uff08mit + Dativ\uff09"},
                {"de": "Er ist in der Schule.", "cn": "\u4ed6\u5728\u5b66\u6821\u91cc\u3002\uff08in + Dativ\uff09"},
                {"de": "Das Bild h\u00e4ngt an der Wand.", "cn": "\u753b\u6302\u5728\u5899\u4e0a\u3002\uff08an + Dativ\uff09"},
            ],
            "table": {
                "\u9633\u6027 der": "dem", "\u9634\u6027 die": "der",
                "\u4e2d\u6027 das": "dem", "\u590d\u6570 die": "den (+n)",
            },
            "tip_cn": "Dativ \u53e3\u8bc0\uff1a\u9633\u4e2d\u53d8 dem\uff0c\u9634\u6027\u53d8 der\uff0c\u590d\u6570 den \u52a0 n\u3002",
        },
        {
            "title": "\u60c5\u6001\u52a8\u8bcd k\u00f6nnen/m\u00fcssen",
            "explanation_cn": (
                "k\u00f6nnen\uff08\u80fd/\u4f1a\uff09\u548c m\u00fcssen\uff08\u5fc5\u987b\uff09\u662f\u6700\u5e38\u7528\u7684\u60c5\u6001\u52a8\u8bcd\u3002"
                "\u60c5\u6001\u52a8\u8bcd\u653e\u5728\u7b2c\u4e8c\u4f4d\uff0c\u5b9e\u4e49\u52a8\u8bcd\u4ee5\u539f\u5f62\u653e\u5728\u53e5\u672b\u3002"
                "ich \u548c er/sie/es \u5f62\u5f0f\u76f8\u540c\u3002"
            ),
            "examples": [
                {"de": "Ich kann Deutsch sprechen.", "cn": "\u6211\u4f1a\u8bf4\u5fb7\u8bed\u3002"},
                {"de": "Du musst jetzt gehen.", "cn": "\u4f60\u73b0\u5728\u5fc5\u987b\u8d70\u4e86\u3002"},
                {"de": "Kannst du mir helfen?", "cn": "\u4f60\u80fd\u5e2e\u6211\u5417\uff1f"},
            ],
            "table": {
                "ich": "kann / muss", "du": "kannst / musst",
                "er/sie/es": "kann / muss", "wir": "k\u00f6nnen / m\u00fcssen",
                "ihr": "k\u00f6nnt / m\u00fcsst", "sie/Sie": "k\u00f6nnen / m\u00fcssen",
            },
            "tip_cn": "\u60c5\u6001\u52a8\u8bcd\u6846\u67b6\uff1a\u60c5\u6001\u52a8\u8bcd\uff08\u7b2c\u4e8c\u4f4d\uff09\u2026 \u5b9e\u4e49\u52a8\u8bcd\u539f\u5f62\uff08\u53e5\u672b\uff09\u3002",
        },
    ],
    6: [
        {
            "title": "\u66f4\u591a\u60c5\u6001\u52a8\u8bcd wollen/d\u00fcrfen/sollen",
            "explanation_cn": (
                "wollen\uff08\u60f3\u8981\uff09\u8868\u8fbe\u5f3a\u70c8\u610f\u613f\uff0c"
                "d\u00fcrfen\uff08\u5141\u8bb8/\u53ef\u4ee5\uff09\u8868\u8fbe\u8bb8\u53ef\uff0c"
                "sollen\uff08\u5e94\u8be5\uff09\u8868\u8fbe\u5efa\u8bae\u6216\u4e49\u52a1\u3002"
                "\u4e09\u8005\u90fd\u662f\u60c5\u6001\u52a8\u8bcd\uff0c\u8bed\u6cd5\u7ed3\u6784\u76f8\u540c\u3002"
            ),
            "examples": [
                {"de": "Ich will nach Hause gehen.", "cn": "\u6211\u60f3\u56de\u5bb6\u3002"},
                {"de": "Darf ich hier rauchen?", "cn": "\u6211\u53ef\u4ee5\u5728\u8fd9\u91cc\u62bd\u70df\u5417\uff1f"},
                {"de": "Du sollst mehr Wasser trinken.", "cn": "\u4f60\u5e94\u8be5\u591a\u559d\u6c34\u3002"},
            ],
            "table": {
                "ich": "will / darf / soll",
                "du": "willst / darfst / sollst",
                "er/sie/es": "will / darf / soll",
                "wir": "wollen / d\u00fcrfen / sollen",
            },
            "tip_cn": "\u8bed\u6c14\u5f3a\u5ea6\uff1awollen\uff08\u60f3\u8981\uff09> m\u00f6chten\uff08\u60f3\u8981\uff0c\u793c\u8c8c\uff09> sollen\uff08\u5e94\u8be5\uff09\u3002",
        },
        {
            "title": "\u73b0\u5728\u5b8c\u6210\u65f6 Perfekt \u5165\u95e8",
            "explanation_cn": (
                "\u5fb7\u8bed\u53e3\u8bed\u4e2d\u5e38\u7528\u73b0\u5728\u5b8c\u6210\u65f6\u8868\u793a\u8fc7\u53bb\u3002"
                "\u7ed3\u6784\uff1ahaben/sein + \u8fc7\u53bb\u5206\u8bcd\u3002"
                "\u89c4\u5219\u52a8\u8bcd\u8fc7\u53bb\u5206\u8bcd\uff1age- + \u8bcd\u5e72 + -t\uff08\u5982 gemacht\uff09\u3002"
            ),
            "examples": [
                {"de": "Ich habe Deutsch gelernt.", "cn": "\u6211\u5b66\u4e86\u5fb7\u8bed\u3002"},
                {"de": "Er hat Fu\u00dfball gespielt.", "cn": "\u4ed6\u8e22\u4e86\u8db3\u7403\u3002"},
                {"de": "Wir haben Pizza gegessen.", "cn": "\u6211\u4eec\u5403\u4e86\u62ab\u8428\u3002"},
            ],
            "table": {
                "machen": "gemacht", "lernen": "gelernt",
                "spielen": "gespielt", "kaufen": "gekauft",
                "essen": "gegessen (\u4e0d\u89c4\u5219)", "trinken": "getrunken (\u4e0d\u89c4\u5219)",
            },
            "tip_cn": "\u89c4\u5219\u8fc7\u53bb\u5206\u8bcd\u516c\u5f0f\uff1age + \u8bcd\u5e72 + t\uff0c\u5982 mach \u2192 gemacht\u3002",
        },
        {
            "title": "\u8fde\u8bcd und/aber/oder",
            "explanation_cn": (
                "und\uff08\u548c\uff09\u3001aber\uff08\u4f46\u662f\uff09\u3001oder\uff08\u6216\u8005\uff09\u662f\u6700\u57fa\u672c\u7684\u5e76\u5217\u8fde\u8bcd\u3002"
                "\u5b83\u4eec\u8fde\u63a5\u4e24\u4e2a\u4e3b\u53e5\uff0c\u4e0d\u6539\u53d8\u8bed\u5e8f\uff08\u52a8\u8bcd\u4ecd\u5728\u7b2c\u4e8c\u4f4d\uff09\u3002"
            ),
            "examples": [
                {"de": "Ich lerne Deutsch und er lernt Englisch.", "cn": "\u6211\u5b66\u5fb7\u8bed\uff0c\u4ed6\u5b66\u82f1\u8bed\u3002"},
                {"de": "Ich bin m\u00fcde, aber ich muss arbeiten.", "cn": "\u6211\u5f88\u7d2f\uff0c\u4f46\u6211\u5fc5\u987b\u5de5\u4f5c\u3002"},
                {"de": "M\u00f6chtest du Tee oder Kaffee?", "cn": "\u4f60\u60f3\u8981\u8336\u8fd8\u662f\u5496\u5561\uff1f"},
            ],
            "table": None,
            "tip_cn": "und/aber/oder \u540e\u9762\u8bed\u5e8f\u4e0d\u53d8\uff0c\u4e3b\u8bed + \u52a8\u8bcd\u6b63\u5e38\u6392\u5217\u3002",
        },
    ],
}


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

    lessons = _GRAMMAR_LESSONS.get(module_id, [])

    return {
        "module_id": module_id,
        "module_name_cn": module.name_cn if module else "综合练习",
        "level": "A1",
        "total": len(exercises),
        "lessons": lessons,
        "exercises": exercises,
    }
