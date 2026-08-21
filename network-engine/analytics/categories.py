APPLICATION_CATEGORIES = {

    "YouTube": "Streaming",

    "Netflix": "Streaming",

    "Instagram": "Social Media",

    "Facebook": "Social Media",

    "TikTok": "Social Media",

    "Discord": "Communication",

    "Telegram": "Communication",

    "Steam": "Gaming",

    "Google": "Cloud",

    "Windows Update": "Downloads",
}


def get_category(application):

    return APPLICATION_CATEGORIES.get(
        application,
        "Other",
    )