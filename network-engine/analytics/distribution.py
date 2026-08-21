from collections import defaultdict


def calculate_distribution(
    application_traffic,
):

    categories = defaultdict(int)

    for item in application_traffic:

        category = item["category"]

        categories[category] += (
            item["bytes"]
        )

    total = sum(
        categories.values()
    )

    if total == 0:
        return {}

    result = {}

    for category, value in categories.items():

        result[category] = {
            "bytes": value,
            "percentage": round(
                (value / total) * 100,
                2,
            ),
        }

    return result