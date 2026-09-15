"""
Calculator tool module for the LangGraph agent.

Provides a Calculator class that can be used as a LangChain tool
to perform mathematical operations and basic statistical operations.
"""

from typing import Union, List
from langchain_core.tools import tool
import math
import numpy as np
from datetime import datetime, timedelta
import pytz


class Calculator:
    """
    A calculator utility class that provides various mathematical operations.
    Can be used directly or wrapped as a LangChain tool.
    """

    @staticmethod
    def add(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Add two numbers."""
        return a + b

    @staticmethod
    def subtract(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Subtract b from a."""
        return a - b

    @staticmethod
    def multiply(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Multiply two numbers."""
        return a * b

    @staticmethod
    def divide(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Divide a by b. Raises ValueError if b is zero."""
        if b == 0:
            raise ValueError("Division by zero is not allowed")
        return a / b

    @staticmethod
    def power(base: Union[int, float], exponent: Union[int, float]) -> Union[int, float]:
        """Raise base to the power of exponent."""
        return base ** exponent

    @staticmethod
    def square_root(n: Union[int, float]) -> float:
        """Calculate the square root of n. Raises ValueError if n is negative."""
        if n < 0:
            raise ValueError("Cannot calculate square root of negative number")
        return math.sqrt(n)

    @staticmethod
    def absolute(n: Union[int, float]) -> Union[int, float]:
        """Return the absolute value of n."""
        return abs(n)

    @staticmethod
    def modulo(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Calculate a modulo b. Raises ValueError if b is zero."""
        if b == 0:
            raise ValueError("Modulo by zero is not allowed")
        return a % b

    @staticmethod
    def floor_divide(a: Union[int, float], b: Union[int, float]) -> Union[int, float]:
        """Perform floor division (a // b). Raises ValueError if b is zero."""
        if b == 0:
            raise ValueError("Floor division by zero is not allowed")
        return a // b

    # ============================================================
    # STATISTICAL OPERATIONS
    # ============================================================

    @staticmethod
    def mean(numbers: List[Union[int, float]]) -> float:
        """Calculate the mean (average) of a list of numbers."""
        if not numbers:
            raise ValueError("Cannot calculate mean of empty list")
        return float(np.mean(numbers))

    @staticmethod
    def median(numbers: List[Union[int, float]]) -> float:
        """Calculate the median of a list of numbers."""
        if not numbers:
            raise ValueError("Cannot calculate median of empty list")
        return float(np.median(numbers))

    @staticmethod
    def std_dev(numbers: List[Union[int, float]], ddof: int = 0) -> float:
        """
        Calculate the standard deviation of a list of numbers.
        
        Args:
            numbers: List of numbers
            ddof: Delta degrees of freedom (0 for population, 1 for sample). Default is 0.
        """
        if not numbers:
            raise ValueError("Cannot calculate standard deviation of empty list")
        if len(numbers) < ddof + 1:
            raise ValueError("Not enough data points for the given ddof")
        return float(np.std(numbers, ddof=ddof))

    @staticmethod
    def variance(numbers: List[Union[int, float]], ddof: int = 0) -> float:
        """
        Calculate the variance of a list of numbers.
        
        Args:
            numbers: List of numbers
            ddof: Delta degrees of freedom (0 for population, 1 for sample). Default is 0.
        """
        if not numbers:
            raise ValueError("Cannot calculate variance of empty list")
        if len(numbers) < ddof + 1:
            raise ValueError("Not enough data points for the given ddof")
        return float(np.var(numbers, ddof=ddof))

    @staticmethod
    def sum_values(numbers: List[Union[int, float]]) -> Union[int, float]:
        """Calculate the sum of a list of numbers."""
        if not numbers:
            return 0
        return float(np.sum(numbers))

    @staticmethod
    def min_value(numbers: List[Union[int, float]]) -> Union[int, float]:
        """Find the minimum value in a list of numbers."""
        if not numbers:
            raise ValueError("Cannot find minimum of empty list")
        return float(np.min(numbers))

    @staticmethod
    def max_value(numbers: List[Union[int, float]]) -> Union[int, float]:
        """Find the maximum value in a list of numbers."""
        if not numbers:
            raise ValueError("Cannot find maximum of empty list")
        return float(np.max(numbers))

    @staticmethod
    def percentile(numbers: List[Union[int, float]], q: Union[int, float]) -> float:
        """
        Calculate the percentile of a list of numbers.
        
        Args:
            numbers: List of numbers
            q: Percentile value (0-100)
        """
        if not numbers:
            raise ValueError("Cannot calculate percentile of empty list")
        if not (0 <= q <= 100):
            raise ValueError("Percentile q must be between 0 and 100")
        return float(np.percentile(numbers, q))

    @staticmethod
    def correlation(x: List[Union[int, float]], y: List[Union[int, float]]) -> float:
        """
        Calculate the Pearson correlation coefficient between two lists.
        
        Raises ValueError if lists have different lengths or less than 2 elements.
        """
        if len(x) != len(y):
            raise ValueError("Lists must have the same length")
        if len(x) < 2:
            raise ValueError("Need at least 2 data points for correlation")
        return float(np.corrcoef(x, y)[0, 1])


# ============================================================
# TIME TOOLS
# ============================================================

class TimeTools:
    """
    A time utility class that provides various datetime operations.
    Can be used directly or wrapped as a LangChain tool.
    """

    @staticmethod
    def get_current_time(timezone: str = "UTC") -> str:
        """Get the current time in a specified timezone (default: UTC)."""
        try:
            tz = pytz.timezone(timezone)
            current_time = datetime.now(tz)
            return current_time.strftime("%Y-%m-%d %H:%M:%S %Z")
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone}")

    @staticmethod
    def get_current_timestamp() -> int:
        """Get the current Unix timestamp (seconds since epoch)."""
        return int(datetime.now().timestamp())

    @staticmethod
    def timestamp_to_datetime(timestamp: int, timezone: str = "UTC") -> str:
        """Convert a Unix timestamp to a readable datetime string in the specified timezone."""
        try:
            tz = pytz.timezone(timezone)
            dt = datetime.fromtimestamp(timestamp, tz)
            return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone}")

    @staticmethod
    def datetime_to_timestamp(date_string: str, timezone: str = "UTC") -> int:
        """Convert a datetime string (YYYY-MM-DD HH:MM:SS) to Unix timestamp."""
        try:
            tz = pytz.timezone(timezone)
            dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            dt = tz.localize(dt)
            return int(dt.timestamp())
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD HH:MM:SS: {e}")
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone}")

    @staticmethod
    def add_days(date_string: str, days: int, timezone: str = "UTC") -> str:
        """Add or subtract days from a date and return the new date."""
        try:
            tz = pytz.timezone(timezone)
            dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            dt = tz.localize(dt)
            new_dt = dt + timedelta(days=days)
            return new_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD HH:MM:SS: {e}")
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone}")

    @staticmethod
    def add_hours(date_string: str, hours: int, timezone: str = "UTC") -> str:
        """Add or subtract hours from a datetime and return the new datetime."""
        try:
            tz = pytz.timezone(timezone)
            dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            dt = tz.localize(dt)
            new_dt = dt + timedelta(hours=hours)
            return new_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD HH:MM:SS: {e}")
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone}")

    @staticmethod
    def add_minutes(date_string: str, minutes: int, timezone: str = "UTC") -> str:
        """Add or subtract minutes from a datetime and return the new datetime."""
        try:
            tz = pytz.timezone(timezone)
            dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            dt = tz.localize(dt)
            new_dt = dt + timedelta(minutes=minutes)
            return new_dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD HH:MM:SS: {e}")
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone}")

    @staticmethod
    def time_difference(start_date: str, end_date: str, timezone: str = "UTC") -> dict:
        """
        Calculate the time difference between two datetime strings.
        Returns days, hours, minutes, and seconds.
        """
        try:
            tz = pytz.timezone(timezone)
            start = datetime.strptime(start_date, "%Y-%m-%d %H:%M:%S")
            end = datetime.strptime(end_date, "%Y-%m-%d %H:%M:%S")
            start = tz.localize(start)
            end = tz.localize(end)
            
            delta = end - start
            total_seconds = int(delta.total_seconds())
            
            days = delta.days
            hours = (total_seconds % (24 * 3600)) // 3600
            minutes = (total_seconds % 3600) // 60
            seconds = total_seconds % 60
            
            return {
                "total_seconds": total_seconds,
                "days": days,
                "hours": hours,
                "minutes": minutes,
                "seconds": seconds,
            }
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD HH:MM:SS: {e}")
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone}")

    @staticmethod
    def get_day_of_week(date_string: str, timezone: str = "UTC") -> str:
        """Get the day of the week for a given date."""
        try:
            tz = pytz.timezone(timezone)
            dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            dt = tz.localize(dt)
            days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
            return days[dt.weekday()]
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD HH:MM:SS: {e}")
        except pytz.exceptions.UnknownTimeZoneError:
            raise ValueError(f"Unknown timezone: {timezone}")

    @staticmethod
    def convert_timezone(date_string: str, from_tz: str, to_tz: str) -> str:
        """Convert a datetime from one timezone to another."""
        try:
            from_timezone = pytz.timezone(from_tz)
            to_timezone = pytz.timezone(to_tz)
            
            dt = datetime.strptime(date_string, "%Y-%m-%d %H:%M:%S")
            dt = from_timezone.localize(dt)
            dt = dt.astimezone(to_timezone)
            
            return dt.strftime("%Y-%m-%d %H:%M:%S %Z")
        except ValueError as e:
            raise ValueError(f"Invalid date format. Use YYYY-MM-DD HH:MM:SS: {e}")
        except pytz.exceptions.UnknownTimeZoneError as e:
            raise ValueError(f"Unknown timezone: {e}")


# ============================================================
# LANGCHAIN TOOL WRAPPERS
# ============================================================
# These decorators convert static methods into LangChain tools
# that can be automatically discovered and bound to the LLM

@tool
def calculate_add(a: float, b: float) -> float:
    """Add two numbers together. Returns their sum."""
    return Calculator.add(a, b)


@tool
def calculate_subtract(a: float, b: float) -> float:
    """Subtract the second number from the first. Returns the difference."""
    return Calculator.subtract(a, b)


@tool
def calculate_multiply(a: float, b: float) -> float:
    """Multiply two numbers together. Returns their product."""
    return Calculator.multiply(a, b)


@tool
def calculate_divide(a: float, b: float) -> float:
    """Divide the first number by the second. Raises an error if dividing by zero."""
    return Calculator.divide(a, b)


@tool
def calculate_power(base: float, exponent: float) -> float:
    """Raise a base number to a given exponent. Returns the result."""
    return Calculator.power(base, exponent)


@tool
def calculate_square_root(n: float) -> float:
    """Calculate the square root of a number. Raises an error for negative numbers."""
    return Calculator.square_root(n)


@tool
def calculate_absolute(n: float) -> float:
    """Return the absolute value (magnitude) of a number."""
    return Calculator.absolute(n)


@tool
def calculate_modulo(a: float, b: float) -> float:
    """Calculate the remainder when a is divided by b."""
    return Calculator.modulo(a, b)


@tool
def calculate_floor_divide(a: float, b: float) -> float:
    """Perform floor division - divide and round down to nearest integer."""
    return Calculator.floor_divide(a, b)


# ============================================================
# STATISTICAL OPERATION TOOLS
# ============================================================

@tool
def calculate_mean(numbers: List[float]) -> float:
    """Calculate the mean (average) of a list of numbers."""
    return Calculator.mean(numbers)


@tool
def calculate_median(numbers: List[float]) -> float:
    """Calculate the median of a list of numbers."""
    return Calculator.median(numbers)


@tool
def calculate_std_dev(numbers: List[float], ddof: int = 0) -> float:
    """
    Calculate the standard deviation of a list of numbers.
    Use ddof=0 for population, ddof=1 for sample.
    """
    return Calculator.std_dev(numbers, ddof)


@tool
def calculate_variance(numbers: List[float], ddof: int = 0) -> float:
    """
    Calculate the variance of a list of numbers.
    Use ddof=0 for population, ddof=1 for sample.
    """
    return Calculator.variance(numbers, ddof)


@tool
def calculate_sum(numbers: List[float]) -> float:
    """Calculate the sum of all numbers in a list."""
    return Calculator.sum_values(numbers)


@tool
def calculate_min(numbers: List[float]) -> float:
    """Find the minimum value in a list of numbers."""
    return Calculator.min_value(numbers)


@tool
def calculate_max(numbers: List[float]) -> float:
    """Find the maximum value in a list of numbers."""
    return Calculator.max_value(numbers)


@tool
def calculate_percentile(numbers: List[float], q: float) -> float:
    """Calculate the percentile (q between 0-100) of a list of numbers."""
    return Calculator.percentile(numbers, q)


@tool
def calculate_correlation(x: List[float], y: List[float]) -> float:
    """Calculate the Pearson correlation coefficient between two lists."""
    return Calculator.correlation(x, y)


# ============================================================
# TIME OPERATION TOOLS
# ============================================================

@tool
def get_current_time(timezone: str = "UTC") -> str:
    """Get the current time in a specified timezone. Default is UTC."""
    return TimeTools.get_current_time(timezone)


@tool
def get_current_timestamp() -> int:
    """Get the current Unix timestamp (seconds since epoch)."""
    return TimeTools.get_current_timestamp()


@tool
def timestamp_to_datetime(timestamp: int, timezone: str = "UTC") -> str:
    """Convert a Unix timestamp to a readable datetime string in the specified timezone."""
    return TimeTools.timestamp_to_datetime(timestamp, timezone)


@tool
def datetime_to_timestamp(date_string: str, timezone: str = "UTC") -> int:
    """Convert a datetime string (YYYY-MM-DD HH:MM:SS) to Unix timestamp."""
    return TimeTools.datetime_to_timestamp(date_string, timezone)


@tool
def add_days_to_date(date_string: str, days: int, timezone: str = "UTC") -> str:
    """Add or subtract days from a date. Use negative numbers to subtract."""
    return TimeTools.add_days(date_string, days, timezone)


@tool
def add_hours_to_date(date_string: str, hours: int, timezone: str = "UTC") -> str:
    """Add or subtract hours from a datetime. Use negative numbers to subtract."""
    return TimeTools.add_hours(date_string, hours, timezone)


@tool
def add_minutes_to_date(date_string: str, minutes: int, timezone: str = "UTC") -> str:
    """Add or subtract minutes from a datetime. Use negative numbers to subtract."""
    return TimeTools.add_minutes(date_string, minutes, timezone)


@tool
def calculate_time_difference(start_date: str, end_date: str, timezone: str = "UTC") -> dict:
    """Calculate the time difference between two datetime strings. Returns days, hours, minutes, seconds."""
    return TimeTools.time_difference(start_date, end_date, timezone)


@tool
def get_day_of_week(date_string: str, timezone: str = "UTC") -> str:
    """Get the day of the week for a given date."""
    return TimeTools.get_day_of_week(date_string, timezone)


@tool
def convert_timezone(date_string: str, from_tz: str, to_tz: str) -> str:
    """Convert a datetime from one timezone to another."""
    return TimeTools.convert_timezone(date_string, from_tz, to_tz)


# Collect all calculator tools in a list for easy integration
CALCULATOR_TOOLS = [
    calculate_add,
    calculate_subtract,
    calculate_multiply,
    calculate_divide,
    calculate_power,
    calculate_square_root,
    calculate_absolute,
    calculate_modulo,
    calculate_floor_divide,
    calculate_mean,
    calculate_median,
    calculate_std_dev,
    calculate_variance,
    calculate_sum,
    calculate_min,
    calculate_max,
    calculate_percentile,
    calculate_correlation,
    get_current_time,
    get_current_timestamp,
    timestamp_to_datetime,
    datetime_to_timestamp,
    add_days_to_date,
    add_hours_to_date,
    add_minutes_to_date,
    calculate_time_difference,
    get_day_of_week,
    convert_timezone,
]


if __name__ == "__main__":
    # Example usage
    print("Calculator Tool Examples:")
    print("\n--- Basic Operations ---")
    print(f"  10 + 5 = {Calculator.add(10, 5)}")
    print(f"  10 - 5 = {Calculator.subtract(10, 5)}")
    print(f"  10 * 5 = {Calculator.multiply(10, 5)}")
    print(f"  10 / 5 = {Calculator.divide(10, 5)}")
    print(f"  2 ^ 8 = {Calculator.power(2, 8)}")
    print(f"  √16 = {Calculator.square_root(16)}")
    print(f"  |-42| = {Calculator.absolute(-42)}")
    print(f"  17 % 5 = {Calculator.modulo(17, 5)}")
    print(f"  17 // 5 = {Calculator.floor_divide(17, 5)}")
    
    print("\n--- Statistical Operations ---")
    data = [10, 20, 30, 40, 50]
    print(f"  Data: {data}")
    print(f"  Mean: {Calculator.mean(data)}")
    print(f"  Median: {Calculator.median(data)}")
    print(f"  Std Dev (population): {Calculator.std_dev(data, ddof=0):.2f}")
    print(f"  Std Dev (sample): {Calculator.std_dev(data, ddof=1):.2f}")
    print(f"  Variance: {Calculator.variance(data):.2f}")
    print(f"  Sum: {Calculator.sum_values(data)}")
    print(f"  Min: {Calculator.min_value(data)}")
    print(f"  Max: {Calculator.max_value(data)}")
    print(f"  75th Percentile: {Calculator.percentile(data, 75)}")
    
    print("\n--- Correlation ---")
    x_data = [1, 2, 3, 4, 5]
    y_data = [2, 4, 5, 4, 6]
    print(f"  X: {x_data}")
    print(f"  Y: {y_data}")
    print(f"  Correlation: {Calculator.correlation(x_data, y_data):.3f}")
    
    print("\n--- Time Operations ---")
    print(f"  Current UTC time: {TimeTools.get_current_time('UTC')}")
    print(f"  Current timestamp: {TimeTools.get_current_timestamp()}")
    
    sample_date = "2026-05-11 10:30:00"
    print(f"  Sample date: {sample_date}")
    print(f"  Add 5 days: {TimeTools.add_days(sample_date, 5, 'UTC')}")
    print(f"  Add 3 hours: {TimeTools.add_hours(sample_date, 3, 'UTC')}")
    print(f"  Add 30 minutes: {TimeTools.add_minutes(sample_date, 30, 'UTC')}")
    print(f"  Day of week: {TimeTools.get_day_of_week(sample_date, 'UTC')}")
    
    start = "2026-05-11 10:00:00"
    end = "2026-05-11 14:30:45"
    diff = TimeTools.time_difference(start, end, 'UTC')
    print(f"  Time diff ({start} to {end}):")
    print(f"    → {diff['hours']}h {diff['minutes']}m {diff['seconds']}s")
    
    print(f"  Convert to EST: {TimeTools.convert_timezone(sample_date, 'UTC', 'US/Eastern')}")
