def validate_required_columns(*args, **kwargs):
    raise NotImplementedError("Shared validators are not implemented yet.")


def validate_trackvia_columns(trackvia_df):
    if trackvia_df is None:
        raise ValueError("TrackVia data is required.")

    if trackvia_df.empty:
        raise ValueError("The TrackVia file is empty. Please provide a file with data.")

    columns = set(trackvia_df.columns)
    missing_columns = []

    if "sku" not in columns:
        missing_columns.append("sku")

    od_inches_columns = {"part_od_inches", "part_od_inches_10", "part_od_inches_range"}
    if not columns.intersection(od_inches_columns):
        missing_columns.append("one of: part_od_inches, part_od_inches_10, part_od_inches_range")

    od_millimeters_columns = {"part_od_mm", "part_od_mm_10", "part_od_mm_range"}
    if not columns.intersection(od_millimeters_columns):
        missing_columns.append("one of: part_od_mm, part_od_mm_10, part_od_mm_range")

    if missing_columns:
        raise ValueError(
            "The TrackVia file is missing required columns: "
            + "; ".join(missing_columns)
            + "."
        )
