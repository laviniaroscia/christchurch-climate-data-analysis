"""Interactive climate data analysis for Christchurch weather stations."""

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


BASE_DIR = Path(__file__).resolve().parent.parent
DATA_DIR = BASE_DIR / "data"

MONTH_NAMES = [
    "January",
    "February",
    "March",
    "April",
    "May",
    "June",
    "July",
    "August",
    "September",
    "October",
    "November",
    "December",
]

LOCATIONS = {
    "Christchurch Aero": (
        DATA_DIR / "rain_aero.csv",
        DATA_DIR / "temperature_aero.csv",
    ),
    "Bromley Ews": (
        DATA_DIR / "rain_bromley.csv",
        DATA_DIR / "temperature_bromley.csv",
    ),
    "Christchurch Gardens": (
        DATA_DIR / "rain_gardens.csv",
        DATA_DIR / "temperature_gardens.csv",
    ),
    "Kyle St Ews": (
        DATA_DIR / "rain_kyle.csv",
        DATA_DIR / "temperature_kyle.csv",
    ),
}


def clean_monthly_data(file_path):
    """Read climate data and remove annual totals and incomplete years."""

    df = pd.read_csv(file_path)

    # The final column contains annual totals and is not required
    # for the monthly analysis.
    df = df.drop(columns=df.columns[-1])

    # Keep only years containing a complete set of monthly observations.
    df = df.dropna()

    return df


def clean_location_data(rain_file, temperature_file):
    """Clean rainfall and temperature data and retain common years."""

    rain_df = clean_monthly_data(rain_file)
    temp_df = clean_monthly_data(temperature_file)

    common_years = set(rain_df["YEAR"]) & set(temp_df["YEAR"])

    rain_df = rain_df[rain_df["YEAR"].isin(common_years)]
    temp_df = temp_df[temp_df["YEAR"].isin(common_years)]

    return rain_df, temp_df


def process_all_locations(location_files):
    """Load and clean climate datasets for all weather stations."""

    cleaned_data = {}

    for location, (rain_file, temp_file) in location_files.items():
        rain_df, temp_df = clean_location_data(rain_file, temp_file)

        cleaned_data[location] = {
            "rain": rain_df,
            "temperature": temp_df,
        }

    return cleaned_data


def select_location(all_data):
    """Allow the user to select one station or all stations."""

    location_names = list(all_data.keys())

    print("\nSelect a location:")

    for index, location in enumerate(location_names):
        print(f"[{index}] {location}")

    all_stations_option = len(location_names)
    print(f"[{all_stations_option}] All Stations")

    choice = input(f"0-{all_stations_option}: ")

    while (
        not choice.isdigit()
        or int(choice) < 0
        or int(choice) > all_stations_option
    ):
        print("Invalid selection.")
        choice = input(f"0-{all_stations_option}: ")

    choice = int(choice)

    if choice == all_stations_option:
        return "All Stations"

    return location_names[choice]


def get_years_for_location(all_data, location):
    """Return years with both rainfall and temperature data."""

    rain_years = set(all_data[location]["rain"]["YEAR"])
    temperature_years = set(all_data[location]["temperature"]["YEAR"])

    return sorted(rain_years & temperature_years)


def get_common_years_all_locations(all_data):
    """Return years available across every weather station."""

    common_years = None

    for location in all_data:
        location_years = set(get_years_for_location(all_data, location))

        if common_years is None:
            common_years = location_years
        else:
            common_years &= location_years

    return sorted(common_years)


def select_year(all_data, location):
    """Allow the user to select an available year."""

    if location == "All Stations":
        available_years = get_common_years_all_locations(all_data)
    else:
        available_years = get_years_for_location(all_data, location)

    print(f"\nAvailable years for {location}:")

    for year in available_years:
        print(year)

    year = input("Select a year: ")

    while not year.isdigit() or int(year) not in available_years:
        print("This year is not available for the selected location.")
        year = input("Select another year: ")

    return int(year)


def create_year_location_table(all_data, year, location):
    """Create a monthly rainfall and temperature table for one station."""

    rain_df = all_data[location]["rain"]
    temperature_df = all_data[location]["temperature"]

    rain_row = rain_df[rain_df["YEAR"] == year]
    temperature_row = temperature_df[temperature_df["YEAR"] == year]

    rain_values = rain_row.drop(columns=["YEAR"]).values.flatten()
    temperature_values = (
        temperature_row.drop(columns=["YEAR"]).values.flatten()
    )

    return pd.DataFrame(
        {
            "Month": MONTH_NAMES,
            "Rainfall (mm)": rain_values,
            "Temperature (°C)": temperature_values,
        }
    )


def create_all_stations_table(all_data, year):
    """Calculate average monthly climate data across all stations."""

    rain_tables = []
    temperature_tables = []

    for location in all_data:
        table = create_year_location_table(all_data, year, location)

        rain_tables.append(table["Rainfall (mm)"])
        temperature_tables.append(table["Temperature (°C)"])

    return pd.DataFrame(
        {
            "Month": MONTH_NAMES,
            "Average Rainfall (mm)": pd.concat(
                rain_tables,
                axis=1,
            ).mean(axis=1),
            "Average Temperature (°C)": pd.concat(
                temperature_tables,
                axis=1,
            ).mean(axis=1),
        }
    )


def print_year_location_data(all_data, year, location):
    """Print monthly climate data for the selected location and year."""

    print(f"\nClimate data for {location} in {year}\n")

    if location == "All Stations":
        output_df = create_all_stations_table(all_data, year)
    else:
        output_df = create_year_location_table(all_data, year, location)

    print(output_df.to_string(index=False))

    return output_df


def get_climate_columns(location):
    """Return rainfall and temperature column names."""

    if location == "All Stations":
        return "Average Rainfall (mm)", "Average Temperature (°C)"

    return "Rainfall (mm)", "Temperature (°C)"


def rainfall_bar_plot(output_df, location, year):
    """Optionally display monthly rainfall as a bar chart."""

    print(
        "\nWould you like to see a bar chart of monthly rainfall?"
    )
    answer = input("[0] Yes\n[1] No\n0-1: ")

    while not answer.isdigit() or int(answer) not in (0, 1):
        print("Invalid selection.")
        answer = input("[0] Yes\n[1] No\n0-1: ")

    if int(answer) == 1:
        return

    rain_column, _ = get_climate_columns(location)

    plt.figure(figsize=(10, 6))
    plt.bar(output_df["Month"], output_df[rain_column])

    plt.title(f"Monthly Rainfall - {location} ({year})")
    plt.xlabel("Month")
    plt.ylabel("Rainfall (mm)")
    plt.xticks(rotation=45)
    plt.tight_layout()
    plt.show()


def climate_line_plot(output_df, location, year):
    """Display monthly rainfall and temperature trends."""

    rain_column, temperature_column = get_climate_columns(location)

    fig, ax1 = plt.subplots(figsize=(10, 6))

    # Rainfall - left y-axis
    line1 = ax1.plot(
        output_df["Month"],
        output_df[rain_column],
        marker="o",
        color="tab:blue",
        label="Rainfall",
    )

    ax1.set_xlabel("Month")
    ax1.set_ylabel("Rainfall (mm)")
    ax1.tick_params(axis="x", rotation=45)

    # Temperature - right y-axis
    ax2 = ax1.twinx()

    line2 = ax2.plot(
        output_df["Month"],
        output_df[temperature_column],
        marker="o",
        color="tab:orange",
        label="Temperature",
    )

    ax2.set_ylabel("Temperature (°C)")

    # Combined legend
    lines = line1 + line2
    labels = [line.get_label() for line in lines]
    ax1.legend(lines, labels, loc="upper right")

    plt.title(f"Climate Trends - {location} ({year})")
    fig.tight_layout()
    plt.show()


def rain_temperature_scatter(output_df, location, year):
    """Display the relationship between temperature and rainfall."""

    rain_column, temperature_column = get_climate_columns(location)

    plt.figure(figsize=(8, 6))

    plt.scatter(
        output_df[temperature_column],
        output_df[rain_column],
    )

    plt.title(
        f"Rainfall vs Temperature - {location} ({year})"
    )
    plt.xlabel("Temperature (°C)")
    plt.ylabel("Rainfall (mm)")
    plt.tight_layout()
    plt.show()


def climate_statistics(output_df, location):
    """Calculate summary climate statistics."""

    rain_column, temperature_column = get_climate_columns(location)

    rainfall_mean = np.mean(output_df[rain_column])
    temperature_mean = np.mean(output_df[temperature_column])

    rainfall_std = np.std(output_df[rain_column])
    temperature_std = np.std(output_df[temperature_column])

    correlation = np.corrcoef(
        output_df[rain_column],
        output_df[temperature_column],
    )[0, 1]

    print("\nClimate Statistics\n")

    print(f"Average rainfall: {rainfall_mean:.2f} mm")
    print(f"Average temperature: {temperature_mean:.2f} °C")
    print(f"Rainfall variability: {rainfall_std:.2f} mm")
    print(f"Temperature variability: {temperature_std:.2f} °C")
    print(f"Rainfall/temperature correlation: {correlation:.2f}")


def main():
    """Run the interactive climate analysis."""

    all_data = process_all_locations(LOCATIONS)

    location = select_location(all_data)
    year = select_year(all_data, location)

    output_df = print_year_location_data(
        all_data,
        year,
        location,
    )

    rainfall_bar_plot(output_df, location, year)
    climate_line_plot(output_df, location, year)
    rain_temperature_scatter(output_df, location, year)

    climate_statistics(output_df, location)


if __name__ == "__main__":
    main()