"""
Functional programming utilities for the GitHub Commit Analyzer.
Provides Result<T, E> type, monadic operations, and function composition.
"""

from typing import TypeVar, Generic, Callable, Union, Iterator, List, Optional, Any
from dataclasses import dataclass
from functools import reduce, wraps
import asyncio
from concurrent.futures import ThreadPoolExecutor, as_completed

# Type variables for generic types
T = TypeVar('T')
E = TypeVar('E')
U = TypeVar('U')
V = TypeVar('V')

# ============================================================================
# Result<T, E> Type for Functional Error Handling
# ============================================================================

@dataclass(frozen=True)
class Ok(Generic[T]):
    """Success case of Result type."""
    value: T
    
    def is_ok(self) -> bool:
        """Check if this is Ok."""
        return True
    
    def is_err(self) -> bool:
        """Check if this is Err."""
        return False
    
    def unwrap(self) -> T:
        """Extract value."""
        return self.value
    
    def unwrap_err(self) -> None:
        """Cannot unwrap error from Ok."""
        raise RuntimeError("Called unwrap_err on Ok value")
    
    def __repr__(self) -> str:
        return f"Ok({self.value})"


@dataclass(frozen=True)
class Err(Generic[E]):
    """Error case of Result type."""
    error: E
    
    def is_ok(self) -> bool:
        """Check if this is Ok."""
        return False
    
    def is_err(self) -> bool:
        """Check if this is Err."""
        return True
    
    def unwrap(self) -> None:
        """Cannot unwrap value from Err."""
        raise RuntimeError(f"Called unwrap on Err value: {self.error}")
    
    def unwrap_err(self) -> E:
        """Extract error."""
        return self.error
    
    def __repr__(self) -> str:
        return f"Err({self.error})"


# Result type as Union of Ok and Err
Result = Union[Ok[T], Err[E]]


# ============================================================================
# Result Type Constructors and Type Guards
# ============================================================================

def ok(value: T) -> Ok[T]:
    """Create a successful Result."""
    return Ok(value)


def err(error: E) -> Err[E]:
    """Create a failed Result."""
    return Err(error)


def is_ok(result: Result[T, E]) -> bool:
    """Check if Result is successful."""
    return isinstance(result, Ok)


def is_err(result: Result[T, E]) -> bool:
    """Check if Result is an error."""
    return isinstance(result, Err)


# ============================================================================
# Monadic Operations for Result Type
# ============================================================================

def map_result(func: Callable[[T], U], result: Result[T, E]) -> Result[U, E]:
    """Apply function to Result value if Ok, pass through if Err."""
    if is_ok(result):
        try:
            return ok(func(result.value))
        except Exception as e:
            return err(e)
    return result


def flat_map(func: Callable[[T], Result[U, E]], result: Result[T, E]) -> Result[U, E]:
    """Apply function that returns Result to Result value if Ok."""
    if is_ok(result):
        try:
            return func(result.value)
        except Exception as e:
            return err(e)
    return result


def map_error(func: Callable[[E], V], result: Result[T, E]) -> Result[T, V]:
    """Transform error type if Err, pass through if Ok."""
    if is_err(result):
        return err(func(result.error))
    return result


def and_then(result: Result[T, E], func: Callable[[T], Result[U, E]]) -> Result[U, E]:
    """Alias for flat_map with arguments flipped."""
    return flat_map(func, result)


def or_else(result: Result[T, E], func: Callable[[E], Result[T, V]]) -> Result[T, V]:
    """Provide alternative Result if current is Err."""
    if is_err(result):
        return func(result.error)
    return result


def unwrap_or(result: Result[T, E], default: T) -> T:
    """Extract value or return default if Err."""
    if is_ok(result):
        return result.value
    return default


def unwrap_or_else(result: Result[T, E], func: Callable[[E], T]) -> T:
    """Extract value or compute from error."""
    if is_ok(result):
        return result.value
    return func(result.error)


def expect(result: Result[T, E], message: str) -> T:
    """Extract value or raise with custom message."""
    if is_ok(result):
        return result.value
    raise RuntimeError(f"{message}: {result.error}")


# ============================================================================
# Result Collection Operations
# ============================================================================

def collect_results(results: List[Result[T, E]]) -> Result[List[T], E]:
    """Collect list of Results into Result of list. Fails on first error."""
    values = []
    for result in results:
        if is_err(result):
            return result
        values.append(result.value)
    return ok(values)


def partition_results(results: List[Result[T, E]]) -> tuple[List[T], List[E]]:
    """Separate successful values from errors."""
    oks = []
    errs = []
    
    for result in results:
        if is_ok(result):
            oks.append(result.value)
        else:
            errs.append(result.error)
    
    return oks, errs


def first_ok(results: List[Result[T, E]]) -> Result[T, List[E]]:
    """Return first successful Result or collect all errors."""
    errors = []
    
    for result in results:
        if is_ok(result):
            return result
        errors.append(result.error)
    
    return err(errors)


# ============================================================================
# Safe Function Wrappers
# ============================================================================

def safe(func: Callable[..., T]) -> Callable[..., Result[T, Exception]]:
    """Wrap function to return Result instead of raising exceptions."""
    @wraps(func)
    def wrapper(*args, **kwargs) -> Result[T, Exception]:
        try:
            return ok(func(*args, **kwargs))
        except Exception as e:
            return err(e)
    return wrapper


def safe_async(func: Callable[..., T]) -> Callable[..., Result[T, Exception]]:
    """Wrap async function to return Result instead of raising exceptions."""
    @wraps(func)
    async def wrapper(*args, **kwargs) -> Result[T, Exception]:
        try:
            result = await func(*args, **kwargs)
            return ok(result)
        except Exception as e:
            return err(e)
    return wrapper


# ============================================================================
# Function Composition
# ============================================================================

def compose(*funcs: Callable) -> Callable:
    """Compose functions right to left: compose(f, g)(x) = f(g(x))."""
    def inner(data):
        return reduce(lambda acc, func: func(acc), reversed(funcs), data)
    return inner


def pipe(data: T, *funcs: Callable) -> Any:
    """Apply functions left to right: pipe(x, f, g) = g(f(x))."""
    return reduce(lambda acc, func: func(acc), funcs, data)


def pipe_result(result: Result[T, E], *funcs: Callable[[T], Result[U, E]]) -> Result:
    """Pipe Result through sequence of Result-returning functions."""
    return reduce(lambda acc, func: flat_map(func, acc), funcs, result)


# ============================================================================
# Currying and Partial Application
# ============================================================================

def curry2(func: Callable[[T, U], V]) -> Callable[[T], Callable[[U], V]]:
    """Curry a 2-argument function."""
    def curried(x: T) -> Callable[[U], V]:
        def partial(y: U) -> V:
            return func(x, y)
        return partial
    return curried


def curry3(func: Callable[[T, U, V], Any]) -> Callable[[T], Callable[[U], Callable[[V], Any]]]:
    """Curry a 3-argument function."""
    def curried(x: T) -> Callable[[U], Callable[[V], Any]]:
        def partial1(y: U) -> Callable[[V], Any]:
            def partial2(z: V) -> Any:
                return func(x, y, z)
            return partial2
        return partial1
    return curried


# ============================================================================
# List Processing Utilities
# ============================================================================

def map_list(func: Callable[[T], U], items: List[T]) -> List[U]:
    """Map function over list."""
    return [func(item) for item in items]


def filter_list(predicate: Callable[[T], bool], items: List[T]) -> List[T]:
    """Filter list by predicate."""
    return [item for item in items if predicate(item)]


def reduce_list(func: Callable[[U, T], U], initial: U, items: List[T]) -> U:
    """Reduce list with function and initial value."""
    return reduce(func, items, initial)


def find_first(predicate: Callable[[T], bool], items: List[T]) -> Optional[T]:
    """Find first item matching predicate."""
    for item in items:
        if predicate(item):
            return item
    return None


def group_by(key_func: Callable[[T], U], items: List[T]) -> dict[U, List[T]]:
    """Group items by key function."""
    groups = {}
    for item in items:
        key = key_func(item)
        if key not in groups:
            groups[key] = []
        groups[key].append(item)
    return groups


# ============================================================================
# Parallel Processing Utilities
# ============================================================================

def parallel_map(func: Callable[[T], U], items: List[T], max_workers: int = 4) -> List[U]:
    """Apply function to items in parallel."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(func, item) for item in items]
        return [future.result() for future in as_completed(futures)]


def parallel_map_result(
    func: Callable[[T], Result[U, E]], 
    items: List[T], 
    max_workers: int = 4
) -> List[Result[U, E]]:
    """Apply Result-returning function to items in parallel."""
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = [executor.submit(func, item) for item in items]
        return [future.result() for future in as_completed(futures)]


async def async_map(func: Callable[[T], U], items: List[T]) -> List[U]:
    """Apply async function to items concurrently."""
    tasks = [func(item) for item in items]
    return await asyncio.gather(*tasks)


async def async_map_result(
    func: Callable[[T], Result[U, E]], 
    items: List[T]
) -> List[Result[U, E]]:
    """Apply async Result-returning function to items concurrently."""
    tasks = [func(item) for item in items]
    return await asyncio.gather(*tasks)


# ============================================================================
# Pipeline Building Utilities
# ============================================================================

class Pipeline:
    """Functional pipeline builder for Result types."""
    
    def __init__(self, initial: Result[T, E]):
        self._result = initial
    
    def map(self, func: Callable[[T], U]) -> 'Pipeline':
        """Apply function to pipeline value."""
        self._result = map_result(func, self._result)
        return self
    
    def flat_map(self, func: Callable[[T], Result[U, E]]) -> 'Pipeline':
        """Apply Result-returning function to pipeline value."""
        self._result = flat_map(func, self._result)
        return self
    
    def map_error(self, func: Callable[[E], V]) -> 'Pipeline':
        """Transform error in pipeline."""
        self._result = map_error(func, self._result)
        return self
    
    def filter(self, predicate: Callable[[T], bool], error: E) -> 'Pipeline':
        """Filter pipeline value with predicate."""
        if is_ok(self._result) and not predicate(self._result.value):
            self._result = err(error)
        return self
    
    def tap(self, func: Callable[[T], None]) -> 'Pipeline':
        """Execute side effect if Ok."""
        if is_ok(self._result):
            func(self._result.value)
        return self
    
    def recover(self, func: Callable[[E], Result[T, V]]) -> 'Pipeline':
        """Recover from error."""
        self._result = or_else(self._result, func)
        return self
    
    def build(self) -> Result[T, E]:
        """Build final Result."""
        return self._result


def pipeline(initial: Result[T, E]) -> Pipeline:
    """Create a new pipeline from Result."""
    return Pipeline(initial)


# ============================================================================
# Validation Combinators
# ============================================================================

def validate_all(*validators: Callable[[T], Result[T, E]]) -> Callable[[T], Result[T, List[E]]]:
    """Combine validators to run all and collect errors."""
    def combined_validator(value: T) -> Result[T, List[E]]:
        errors = []
        for validator in validators:
            result = validator(value)
            if is_err(result):
                errors.append(result.error)
        
        if errors:
            return err(errors)
        return ok(value)
    
    return combined_validator


def validate_any(*validators: Callable[[T], Result[T, E]]) -> Callable[[T], Result[T, List[E]]]:
    """Combine validators where any success is sufficient."""
    def combined_validator(value: T) -> Result[T, List[E]]:
        errors = []
        for validator in validators:
            result = validator(value)
            if is_ok(result):
                return result
            errors.append(result.error)
        
        return err(errors)
    
    return combined_validator


# ============================================================================
# Utility Functions for Common Patterns
# ============================================================================

def try_parse_int(value: str) -> Result[int, ValueError]:
    """Safely parse string to integer."""
    try:
        return ok(int(value))
    except ValueError as e:
        return err(e)


def try_parse_float(value: str) -> Result[float, ValueError]:
    """Safely parse string to float."""
    try:
        return ok(float(value))
    except ValueError as e:
        return err(e)


def safe_get(dictionary: dict, key: str) -> Result[Any, KeyError]:
    """Safely get value from dictionary."""
    try:
        return ok(dictionary[key])
    except KeyError as e:
        return err(e)


def safe_index(lst: List[T], index: int) -> Result[T, IndexError]:
    """Safely get item from list by index."""
    try:
        return ok(lst[index])
    except IndexError as e:
        return err(e)


def not_none(value: Optional[T], error: E) -> Result[T, E]:
    """Convert Optional to Result."""
    if value is None:
        return err(error)
    return ok(value)