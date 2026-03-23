import logging

import httpx

from app.config import settings

logger = logging.getLogger(__name__)

# YouTube API 키 없을 때 Fallback 콘텐츠
FALLBACK_VIDEOS = [
    {
        "title": "취준생 응원 영상 | 힘들 때 보세요",
        "video_id": "dQw4w9WgXcQ",
        "url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "channel": "응원 채널",
    },
    {
        "title": "면접 자신감 높이는 5가지 방법",
        "video_id": "example2",
        "url": "https://www.youtube.com/results?search_query=취준생+동기부여",
        "channel": "커리어 코칭",
    },
    {
        "title": "취업 실패 후 다시 일어서는 법",
        "video_id": "example3",
        "url": "https://www.youtube.com/results?search_query=취준생+응원",
        "channel": "멘탈 케어",
    },
]

FALLBACK_QUOTES = [
    {"text": "실패는 성공의 어머니다.", "author": "토마스 에디슨"},
    {"text": "포기하지 않는 한, 실패란 없다.", "author": "앤 설리번"},
    {"text": "오늘의 고생이 내일의 나를 만든다.", "author": "알 수 없음"},
    {"text": "가장 어두운 밤도 끝나고 해는 뜬다.", "author": "빅토르 위고"},
]

MOOD_KEYWORDS = {
    "depressed": "취준생 응원 희망",
    "anxious": "불안 극복 마인드셋",
    "frustrated": "좌절 극복 동기부여",
    "tired": "번아웃 회복 휴식",
    "hopeful": "취업 성공 후기",
}


async def get_motivation_content(
    mood: str = "depressed",
    content_type: str = "mixed",
) -> dict:
    """사용자 상태에 맞는 동기부여 콘텐츠를 추천합니다."""
    videos: list[dict] = []
    quotes: list[dict] = FALLBACK_QUOTES[:3]

    # YouTube Data API 호출
    if settings.youtube_api_key:
        try:
            videos = await _search_youtube(mood)
        except Exception as e:
            logger.warning(f"YouTube API 실패: {e}")
            videos = FALLBACK_VIDEOS
    else:
        videos = FALLBACK_VIDEOS

    result: dict = {"mood": mood}

    if content_type == "video":
        result["videos"] = videos
    elif content_type == "quote":
        result["quotes"] = quotes
    else:
        result["videos"] = videos
        result["quotes"] = quotes

    return result


async def _search_youtube(mood: str) -> list[dict]:
    """YouTube Data API v3로 동기부여 영상 검색."""
    keyword = MOOD_KEYWORDS.get(mood, "취준생 동기부여")
    query = f"취준생 {keyword}"

    url = "https://www.googleapis.com/youtube/v3/search"
    params = {
        "key": settings.youtube_api_key,
        "q": query,
        "part": "snippet",
        "type": "video",
        "maxResults": "5",
        "relevanceLanguage": "ko",
        "videoDuration": "medium",
        "order": "relevance",
    }

    async with httpx.AsyncClient(timeout=10) as client:
        resp = await client.get(url, params=params)
        resp.raise_for_status()
        data = resp.json()

    videos = []
    for item in data.get("items", []):
        vid = item["id"].get("videoId", "")
        snippet = item.get("snippet", {})
        videos.append({
            "title": snippet.get("title", ""),
            "video_id": vid,
            "url": f"https://www.youtube.com/watch?v={vid}",
            "channel": snippet.get("channelTitle", ""),
            "thumbnail": snippet.get("thumbnails", {}).get("medium", {}).get("url", ""),
        })

    return videos
