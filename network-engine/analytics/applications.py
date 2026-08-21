APPLICATION_RULES = {

    "YouTube": [
        "youtube.com",
        "googlevideo.com",
        "ytimg.com",
    ],

    "Google": [
        "google.com",
        "googleapis.com",
        "gstatic.com",
    ],

    "Instagram": [
        "instagram.com",
        "cdninstagram.com",
    ],

    "Facebook": [
        "facebook.com",
        "fbcdn.net",
        "fb.com",
    ],

    "TikTok": [
        "tiktok.com",
        "tiktokcdn.com",
    ],

    "Netflix": [
        "netflix.com",
        "nflxvideo.net",
        "nflximg.net",
    ],

    "Discord": [
        "discord.com",
        "discordapp.com",
    ],

    "Telegram": [
        "telegram.org",
        "t.me",
    ],

    "Steam": [
        "steampowered.com",
        "steamcommunity.com",
        "steamcontent.com",
    ],
}


def detect_application(
    domain,
):

    domain = domain.lower()

    for application, domains in (
        APPLICATION_RULES.items()
    ):

        for pattern in domains:

            if (
                domain == pattern
                or domain.endswith(
                    "." + pattern
                )
            ):

                return application

    return "Unknown"