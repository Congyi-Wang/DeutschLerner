"""A1 curriculum definition — 6 modules with progression by vocab count."""

from dataclasses import dataclass, field


@dataclass
class A1Module:
    """A single A1 curriculum module."""

    id: int
    name_de: str
    name_cn: str
    description_cn: str
    topics: list[str]
    grammar_focus: list[str]
    vocab_themes: list[str]
    target_vocab: int  # vocab count threshold to complete this module


A1_MODULES = [
    A1Module(
        id=1,
        name_de="Begrüßung & persönliche Informationen",
        name_cn="问候与个人信息",
        description_cn="学习基本的打招呼、自我介绍、告别用语",
        topics=[
            "打招呼和问候 (Hallo, Guten Tag, Wie geht's)",
            "自我介绍 (Ich heiße..., Ich komme aus...)",
            "告别用语 (Tschüs, Auf Wiedersehen)",
            "基本礼貌用语 (bitte, danke, Entschuldigung)",
            "认识新朋友 (Woher kommst du? Was machst du?)",
        ],
        grammar_focus=[
            "sein 动词变位 (ich bin, du bist, er/sie ist)",
            "人称代词 (ich, du, er, sie, wir)",
            "基本语序: 主语 + 动词",
        ],
        vocab_themes=["问候", "国家", "职业", "礼貌用语"],
        target_vocab=40,
    ),
    A1Module(
        id=2,
        name_de="Zahlen, Datum & Tagesablauf",
        name_cn="数字、日期与日常作息",
        description_cn="学习数字、时间表达、一天的活动安排",
        topics=[
            "数字1到100 (eins, zwei, drei...)",
            "时间和钟点 (Wie spät ist es? Es ist drei Uhr.)",
            "星期和月份 (Montag, Januar...)",
            "我的一天 (aufstehen, frühstücken, arbeiten)",
            "日常作息时间 (Um 7 Uhr stehe ich auf.)",
        ],
        grammar_focus=[
            "规则动词现在时变位 (machen, spielen, lernen)",
            "时间表达 (um + 时刻)",
            "基本疑问词 (wann, wie viel, was)",
        ],
        vocab_themes=["数字", "时间", "星期", "日常动词"],
        target_vocab=90,
    ),
    A1Module(
        id=3,
        name_de="Familie, Hobbys & Freizeit",
        name_cn="家庭、爱好与休闲",
        description_cn="学习描述家庭成员、谈论兴趣爱好和休闲活动",
        topics=[
            "我的家庭 (Mutter, Vater, Bruder, Schwester)",
            "兴趣爱好 (Ich spiele gern Fußball.)",
            "周末活动 (Am Wochenende gehe ich ins Kino.)",
            "运动和音乐 (schwimmen, Gitarre spielen)",
            "朋友和聚会 (Freunde treffen, zusammen kochen)",
        ],
        grammar_focus=[
            "haben 动词变位 (ich habe, du hast...)",
            "否定: nicht 和 kein",
            "gern / nicht gern 表达喜好",
        ],
        vocab_themes=["家庭成员", "爱好", "运动", "休闲活动"],
        target_vocab=150,
    ),
    A1Module(
        id=4,
        name_de="Einkaufen, Essen & Wegbeschreibung",
        name_cn="购物、饮食与问路",
        description_cn="学习超市购物、餐厅点餐、问路和指路",
        topics=[
            "在超市购物 (Ich brauche Milch und Brot.)",
            "在餐厅点餐 (Ich hätte gern eine Suppe.)",
            "食物和饮料 (Obst, Gemüse, Kaffee, Tee)",
            "问路 (Wo ist der Bahnhof? Gehen Sie geradeaus.)",
            "价格和付款 (Was kostet das? Das macht 5 Euro.)",
        ],
        grammar_focus=[
            "冠词: der, die, das / ein, eine",
            "第四格 (Akkusativ) 基础: Ich kaufe einen Apfel.",
            "möchten (想要) 的用法",
        ],
        vocab_themes=["食物", "饮料", "商店", "方向"],
        target_vocab=220,
    ),
    A1Module(
        id=5,
        name_de="Wohnung, Reise & Verkehr",
        name_cn="住房、旅行与交通",
        description_cn="学习描述住所、出行方式、预订和公共交通",
        topics=[
            "我的房间和家具 (Küche, Schlafzimmer, Tisch, Stuhl)",
            "找房子 (Die Wohnung hat zwei Zimmer.)",
            "公共交通 (Bus, U-Bahn, Straßenbahn)",
            "买火车票 (Eine Fahrkarte nach Berlin, bitte.)",
            "旅行计划 (Ich fahre nach München.)",
        ],
        grammar_focus=[
            "介词: in, auf, an, nach, zu",
            "第三格 (Dativ) 基础: Ich bin in der Küche.",
            "情态动词: können, müssen",
        ],
        vocab_themes=["房间", "家具", "交通工具", "旅行"],
        target_vocab=300,
    ),
    A1Module(
        id=6,
        name_de="Gesundheit, Wetter & Alltag",
        name_cn="健康、天气与日常生活",
        description_cn="学习看医生、描述天气、日常事务和简单叙述",
        topics=[
            "身体部位和健康 (Kopf, Bauch — Mir tut der Kopf weh.)",
            "看医生 (Ich habe Fieber. Ich brauche einen Termin.)",
            "天气描述 (Es regnet. Es ist kalt.)",
            "季节和衣服 (Im Winter trage ich einen Mantel.)",
            "在邮局和银行 (Ich möchte ein Paket schicken.)",
        ],
        grammar_focus=[
            "情态动词: wollen, dürfen, sollen",
            "现在完成时入门: Ich habe gegessen.",
            "连词: und, aber, oder",
        ],
        vocab_themes=["身体", "健康", "天气", "衣服"],
        target_vocab=400,
    ),
]

# Index modules by id for fast lookup
_MODULE_MAP = {m.id: m for m in A1_MODULES}


def get_current_module(vocab_count: int) -> A1Module | None:
    """Determine the current module based on total vocabulary count.

    Returns None if A1 is completed (vocab_count >= 400).
    """
    for module in A1_MODULES:
        if vocab_count < module.target_vocab:
            return module
    return None  # A1 completed


def get_module_by_id(module_id: int) -> A1Module | None:
    """Get a module by its ID."""
    return _MODULE_MAP.get(module_id)


def get_module_progress(vocab_count: int) -> dict:
    """Get progress info for the current level.

    Returns a dict with: level, module info, progress_percent, vocab details,
    and list of all modules.
    """
    module = get_current_module(vocab_count)

    all_modules = [
        {
            "id": m.id,
            "name_de": m.name_de,
            "name_cn": m.name_cn,
            "target_vocab": m.target_vocab,
            "completed": vocab_count >= m.target_vocab,
        }
        for m in A1_MODULES
    ]

    if module is None:
        # A1 completed
        return {
            "level": "A1",
            "completed": True,
            "module_id": None,
            "module_name_de": None,
            "module_name_cn": None,
            "module_description_cn": None,
            "progress_percent": 100,
            "vocab_count": vocab_count,
            "target_vocab": 400,
            "total_modules": 6,
            "current_module_num": 6,
            "all_modules": all_modules,
        }

    # Calculate progress within current module
    prev_target = A1_MODULES[module.id - 2].target_vocab if module.id > 1 else 0
    module_range = module.target_vocab - prev_target
    module_progress = vocab_count - prev_target
    progress_pct = int(module_progress / module_range * 100) if module_range > 0 else 0
    progress_pct = max(0, min(progress_pct, 100))

    return {
        "level": "A1",
        "completed": False,
        "module_id": module.id,
        "module_name_de": module.name_de,
        "module_name_cn": module.name_cn,
        "module_description_cn": module.description_cn,
        "progress_percent": progress_pct,
        "vocab_count": vocab_count,
        "target_vocab": module.target_vocab,
        "total_modules": 6,
        "current_module_num": module.id,
        "all_modules": all_modules,
    }
