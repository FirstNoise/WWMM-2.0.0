# core/character_manager.py
from pathlib import Path
import sys

def _icons_dir() -> str:
    """
    프로젝트 루트/resources/icons 고정
    - 이 파일 경로: <project_root>/ui/components/character_manager.py
    - 아이콘 경로 : <project_root>/resources/icons
    - PyInstaller 실행 파일 환경도 지원
    """
    meipass = getattr(sys, "_MEIPASS", None)
    root = Path(meipass) if meipass else Path(__file__).resolve().parents[1]
    return str(root / "resources" / "icons")

def _icon(path_name: str) -> str:
    return str(Path(_icons_dir()) / path_name)

def get_character_data():
    categories = {
        "기류": ["유노", "카르티시아", "샤콘", "감심", "양양", "기염", "알토"],
        "용융": ["갈브레나", "루파", "장리", "앙코", "치샤", "브렌트", "모르테피"],
        "인멸": ["플로로", "칸타렐라", "로코코", "카멜리아", "도기", "단근"],
        "회절": ["젠니", "페비", "파수인", "금희", "벨리나"],
        "응결": ["카를로타", "절지", "유호", "산화", "설지", "능양"],
        "전도": ["아우구스타", "음림", "상리요", "카카루", "루미", "연무"],
    }
    wanderer = ["방랑자"]

    category_icons = {
        "기류": _icon("ic_기류.png"),
        "용융": _icon("ic_용융.png"),
        "인멸": _icon("ic_인멸.png"),
        "회절": _icon("ic_회절.png"),
        "응결": _icon("ic_응결.png"),
        "전도": _icon("ic_전도.png"),
    }

    # 필요한 캐릭터만 발췌 예시. 전체는 같은 방식으로 나열
    char_icons = {
        "방랑자": "/resources/icons/char_방랑자.png",
        "갈브레나": _icon("char_갈브레나.png"),
        "유노": _icon("char_유노.png"),
        "아우구스타": _icon("char_아우구스타.png"),
        "플로로": _icon("char_플로로.png"),
        "루파": _icon("char_루파.png"),
        "카르티시아": _icon("char_카르티시아.png"),
        "샤콘": _icon("char_샤콘.png"),
        "젠니": _icon("char_젠니.png"),
        "칸타렐라": _icon("char_칸타렐라.png"),
        "페비": _icon("char_페비.png"),
        "로코코": _icon("char_로코코.png"),
        "카를로타": _icon("char_카를로타.png"),
        "카멜리아": _icon("char_카멜리아.png"),
        "파수인": _icon("char_파수인.png"),
        "절지": _icon("char_절지.png"),
        "장리": _icon("char_장리.png"),
        "금희": _icon("char_금희.png"),
        "음림": _icon("char_음림.png"),
        "벨리나": _icon("char_벨리나.png"),
        "앙코": _icon("char_앙코.png"),
        "감심": _icon("char_감심.png"),
        "브렌트": _icon("char_브렌트.png"),
        "상리요": _icon("char_상리요.png"),
        "기염": _icon("char_기염.png"),
        "카카루": _icon("char_카카루.png"),
        "능양": _icon("char_능양.png"),
        "루미": _icon("char_루미.png"),
        "유호": _icon("char_유호.png"),
        "양양": _icon("char_양양.png"),
        "산화": _icon("char_산화.png"),
        "설지": _icon("char_설지.png"),
        "치샤": _icon("char_치샤.png"),
        "단근": _icon("char_단근.png"),
        "도기": _icon("char_도기.png"),
        "모르테피": _icon("char_모르테피.png"),
        "연무": _icon("char_연무.png"),
        "알토": _icon("char_알토.png"),
    }

    category_colors = {
        "기류": "#00b894",
        "용융": "#e17055",
        "인멸": "#6c3483",
        "회절": "#fdcb6e",
        "응결": "#5e8ca6",
        "전도": "#a29bfe",
    }

    return {
        "categories": categories,
        "wanderer": wanderer,
        "category_icons": category_icons,
        "char_icons": char_icons,
        "category_colors": category_colors,
    }
