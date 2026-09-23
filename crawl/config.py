"""Crawler configuration, query strategies, and disease taxonomy."""

from src.config import COFFEE_CLASSES, RICE_CLASSES

CROP_CLASSES: dict[str, list[str]] = {
    "rice": RICE_CLASSES,
    "coffee": COFFEE_CLASSES,
}

CROP_SEARCH_STRATEGIES: dict[str, dict[str, list[str]]] = {
    "rice": {
        "BrownSpot": [
            "Bệnh đốm nâu hại lúa site",
            "triệu chứng đốm nâu lúa site",
            "hình ảnh bệnh đốm nâu lúa site",
            "rice brown spot disease leaf symptoms",
        ],
        "LeafBlast": [
            "Bệnh đạo ôn hại lúa site",
            "bệnh đạo ôn lúa site",
            "hình ảnh bệnh đạo ôn lúa site",
            "rice leaf blast symptoms Magnaporthe",
        ],
        "Hispa": [
            "Bọ gai hại lúa site",
            "hình ảnh bọ gai lúa site",
            "rice hispa beetle damage leaves",
        ],
        "Healthy": [
            "Lúa khỏe mạnh site",
            "cây lúa phát triển tốt site",
            "healthy green rice leaf field",
        ],
    },
    "coffee": {
        "LeafMiner": [
            "Bệnh sâu vẽ bùa cà phê site",
            "hình ảnh bệnh sâu vẽ bùa trên lá cà phê site",
            "coffee leaf miner Leucoptera damage",
        ],
        "PowderyMildew": [
            "Bệnh phấn trắng cà phê site",
            "hình ảnh bệnh phấn trắng hại cà phê site",
            "coffee powdery mildew symptoms",
        ],
        "Rust": [
            "Bệnh nấm rỉ sắt cà phê site",
            "bệnh rỉ sắt hại cà phê site",
            "hình ảnh bệnh gỉ sắt cà phê site",
            "coffee leaf rust Hemileia vastatrix pustules",
        ],
        "AlgalLeafSpot": [
            "Bệnh đốm rong cà phê site",
            "hình ảnh bệnh đốm rong trên lá cà phê site",
            "coffee algal leaf spot Cephaleuros",
        ],
    },
}

DEFAULT_CRAWL_CONFIG = {
    "max_concurrent_scrapes": 5,
    "max_concurrent_ai": 2,
    "timeout": 30.0,
}
