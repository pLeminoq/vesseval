"""
Implementation of states.
"""

from typing import Any, Callable, Dict, List, Optional, Union
from typing_extensions import Self


class State(object):
    """
    A state is a reactive wrapping around values.

    It contains a list of callbacks.
    Callbacks are registered with `on_change` and called when `notify_change` is triggered.
    Note that all attributes of a state that start with an underscore are private, not wrapped and changes are not tracked.
    Regarding higher states, note that you can use `with <state>:` to change multiple values before notifying.
    """

    def __init__(self):
        self._callbacks: List[Callable[[Self], None]] = []
        self._active = True
        self._enter_count = 0

    def on_change(self, callback: Callable[[Self], None], trigger: bool = False) -> int:
        """
        Register a callback on this state.

        Parameters
        ----------
        callback: callable
            the callable to be registered
        trigger: bool
            if true, call the callback after registering

        Returns
        -------
        int
            an id of the callback which can be used to remove it
        """
        self._callbacks.append(callback)

        if trigger:
            callback(self)

        return len(self._callbacks) - 1

    def remove_callback(self, callback_or_id: Union[Callable[[Self], None], int]):
        if type(callback_or_id) is int:
            self._callbacks.pop(callback_or_id)
        else:
            self._callbacks.remove(callback_or_id)

    def notify_change(self):
        """
        Notify all callbacks that this state has changed.
        """
        if not self._active:
            return

        for cb in self._callbacks:
            cb(self)

    def __enter__(self):
        self._enter_count += 1
        self._active = False
        return self

    def __exit__(self, *args):
        self._enter_count = max(self._enter_count - 1, 0)
        if self._enter_count == 0:
            self._active = True
            self.notify_change()

class ElementObserver:

    def __init__(self, list_state: "ListState"):
        self._callbacks = []
        self._list_state = list_state

    def __call__(self, state: State):
        for cb in self._callbacks:
            cb(self._list_state)

class ListState(State):

    def __init__(self, _list: List[State] = []):
        super().__init__()

        self._elem_obs = ElementObserver(self)

        self._list = []
        self.extend(_list)

    def on_change(self, callback: Callable[[Self], None], trigger: bool = False, recursive=False) -> int:
        if recursive:
            self._elem_obs._callbacks.append(callback)

        return super().on_change(callback, trigger=trigger)

    def remove_callback(self, callback_or_id: Union[Callable[[Self], None], int]):
        if type(callback_or_id) is int:
            cb = self._callbacks.pop(callback_or_id)
        else:
            self._callbacks.remove(callback_or_id)
            cb = callback_or_id

        if cb in self._elem_obs._callbacks:
            self._elem_obs._callbacks.remove(cb)

    def append(self, elem: State):
        self._list.append(elem)
        
        elem.on_change(self._elem_obs)

        self.notify_change()

    def clear(self):
        for elem in self._list:
            elem.remove_callback(self._elem_obs)

        self._list.clear()

        self.notify_change()

    def extend(self, _list: List[State]):
        # use `with` to notify just once after appending all elements
        with self:
            for elem in _list:
                self.append(elem)

    def insert(self, index: int, elem: State):
        self._list.insert(index, elem)

        elem.on_change(self._elem_obs)

        self.notify_change()

    def pop(self, index: int = -1) -> State:
        elem = self._list.pop(index)

        elem.remove_callback(self._elem_obs)

        self.notify_change()

        return elem

    def remove(self, elem: State):
        self._list.remove(elem)

        elem.remove_callback(self._elem_obs)
        
        self.notify_change()

    def reverse(self):
        self._list.reverse()
        self.notify_change()

    def sort(self):
        self._list.sort()
        self.notify_change()

    def __getitem__(self, i: int) -> State:
        return self._list[i]

    def count(self) -> int:
        return self._list.count()

    def index(self, elem: State) -> int:
        return self._list.index(elem)

    def __iter__(self):
        return iter(self._list)

    def __len__(self):
        return len(self._list)

    def serialize(self):
        return [value.serialize() for value in self]

    def deserialize(self, _list: List[Dict[str, Any]]):
        raise TypeError(
            "Unable to deserialize list state, since types of elements in list are unknown"
        )


class BasicState(State):
    """
    A basic state contains a single value.

    Notifications are triggered on reassignment of the value.
    For primitive values, such as int and string, notifications are only triggered
    if the value changed on reassignment.
    """

    def __init__(self, value: Any, verify_change=True):
        """
        Initialize a basic state:

        Parameters
        ----------
        value: any
            the internal value of the state
        verify_change: bool, true per default
            verify if the value has changed on reassignment
        """
        super().__init__()

        self._verify_change = verify_change

        self.value = value

    def __setattr__(self, name, new_value):
        # ignore private attributes (begin with an underscore)
        if name[0] == "_":
            super().__setattr__(name, new_value)
            return

        # get the previous value for this attribute
        try:
            old_value = getattr(self, name)
        except AttributeError:
            # initial assignment
            super().__setattr__(name, new_value)
            return

        # verify if the attribute changed
        if self._verify_change and new_value == old_value:
            return

        # update the attribute
        super().__setattr__(name, new_value)

        # notify that the value changed
        self.notify_change()

    def set(self, value: Any):
        """
        Simple function for the assignment of the value.

        This function is typically used in lambda functions where assignments are not possible.

        Parameters
        ----------
        value: any
            the new value
        """
        self.value = value

    def depends_on(
        self, states: List[State], compute_value: Callable[[None], Any], init=False, recursive=False,
    ):
        for state in states:
            if issubclass(type(state), ListState):
                state.on_change(lambda _: self.set(compute_value()), recursive=recursive)
                continue

            state.on_change(lambda _: self.set(compute_value()))

        self.set(compute_value())

    def transform(self, self_to_other: Callable[[State], State]):
        other_state = self_to_other(self)
        self.on_change(lambda _self: other_state.set(self_to_other(_self).value))
        return other_state

    def create_transformed_state(
        self,
        self_to_other: Callable[[Any], Any],
        other_to_self: Callable[[Any], Any] = None,
    ) -> Self:
        """
        Create a transformed basic state.

        E.g., this can be used to create a scaled state of a number.
        Note that both callables need to create an identity mapping: x = other_to_self(self_to_other(x)).
        Otherwise, value notifications will never stop.

        Parameters
        ----------
        self_to_other: callable
            map the current state to the transformed state
        other_to_self: callable
            map the transformed state back to the current state

        Returns
        -------
        a transformed state based on calling self_to_other with the current state
        """
        other = type(self)(self_to_other(self.value))
        self.on_change(
            lambda state: setattr(other, "value", self_to_other(state.value))
        )
        if other_to_self is not None:
            other.on_change(
                lambda state: setattr(self, "value", other_to_self(state.value))
            )
        return other

    def __repr__(self):
        return f"{type(self).__name__}[value={self.value}]"

    def serialize(self):
        return self.value


class IntState(BasicState):
    """
    Implementation of the `BasicState` for an int.
    """

    def __init__(self, value: int):
        super().__init__(value, verify_change=True)


class FloatState(BasicState):
    """
    Implementation of the `BasicState` for a float.

    Float states implement rounding of the number by specifying the desired precision.
    """

    def __init__(
        self, value: float, verify_change=True, precision: Optional[int] = None
    ):
        self._precision = precision

        super().__init__(value)

    def __setattr__(self, name, new_value):
        if name == "value" and self._precision is not None:
            # apply precision if defined
            new_value = round(new_value, ndigits=self._precision)

        super().__setattr__(name, new_value)


class StringState(BasicState):
    """
    Implementation of the `BasicState` for a string.
    """

    def __init__(self, value: str, verify_change=True):
        super().__init__(value)

    def __repr__(self):
        return f'{type(self).__name__}[value="{self.value}"]'

    def to_tk_string_var(self):
        """
        Create a `tk.StringVar` connected to this `StringState`.

        This means that both will have the same value all the time.

        Returns
        -------
        tk.StringVar
        """
        import tkinter as tk

        string_var = tk.StringVar(value=self.value)
        string_var.trace_add("write", lambda *args: self.set(string_var.get()))
        self.on_change(lambda state: string_var.set(self.value))
        return string_var


class BoolState(BasicState):
    """
    Implementation of the `BasicState` for a bool.
    """

    def __init__(self, value: bool, verify_change=True):
        super().__init__(value)


class ObjectState(BasicState):
    """
    Implementation of the `BasicState` for objects.

    This implementation does not verify changes of the internal value.
    Thus, the equals check to verify if the value changed is skipped.
    """

    def __init__(self, value: Any):
        super().__init__(value, verify_change=False)

    def serialize(self):
        raise TypeError(f"Unable to serialize general object state")


# Mapping of primitive values types to their states.
BASIC_STATE_DICT = {
    str: StringState,
    int: IntState,
    float: FloatState,
    bool: BoolState,
}


class HigherState(State):
    """
    A higher state is a collection of other states.

    A higher state automatically notifies a change if one of its internal states change.
    If a value (not a state) is added to a higher state, it will automatically be wrapped into
    a state type.
    """

    def __init__(self):
        super().__init__()

    def __setattr__(self, name, new_value):
        # ignore private attributes (begin with an underscore)
        if name[0] == "_":
            super().__setattr__(name, new_value)
            return

        # wrap non-state values into states
        if not issubclass(type(new_value), State):
            new_value = BASIC_STATE_DICT.get(type(new_value), ObjectState)(new_value)

        # assert that states are not reassigned as only their values should change
        assert not hasattr(self, name) or callable(
            getattr(self, name)
        ), f"Reassignment of value {name} in state {self}"
        # assert that all attributes are states
        assert issubclass(
            type(new_value), State
        ), f"Values of higher states must be states not {type(new_value)}"

        # update the attribute
        super().__setattr__(name, new_value)

        # register notification to the internal state
        new_value.on_change(lambda _: self.notify_change())

    def dict(self):
        """
        Create a dictionary mapping names to states of all internal states.

        Returns
        -------
        Dict[str, State]
        """
        labels = list(filter(lambda l: not l.startswith("_"), self.__dict__.keys()))
        return dict([(label, self.__getattribute__(label)) for label in labels])

    def serialize(self):
        res = {}
        for key, value in self.dict().items():
            try:
                res[key] = value.serialize()
            except TypeError:
                pass
        return res

    def deserialize(self, _dict: Dict[str, Any]) -> Self:
        with self:
            for key, value in _dict.items():
                attr = self.__getattribute__(key)

                if issubclass(type(attr), BasicState):
                    attr._active = False
                    attr.value = value
                    attr._active = True
                    continue

                attr.deserialize(value)

        # pass
        # with self:
        # for key, value in _dict.items():

    def __str__(self, padding=0):
        _strs = []
        for key, value in self.dict().items():
            if issubclass(type(value), HigherState):
                _strs.append(f"{key}{value.__str__(padding=padding+1)}")
            else:
                _strs.append(f"{key}: {value}")

        _padding = " " * padding
        return f"[{type(self).__name__}]:\n{_padding} - " + f"\n{_padding} - ".join(
            _strs
        )


def computed_state(func: Callable[[State], State]):
    """
    Computed annotation for states.

    A computed state is computed from one or more other states.
    It is defined by a computation function.
    A computed state can either be defined by a separate function or as a function and
    state of a higher state.

    Example:
    class SquareNumber(HigherState):

        def __init__(self, number: int):
            super().__init__()

            self.number = number
            self.squared = self.squared(self.number)

        @computed
        def squared(self, number: IntState):
            return IntState(number.value * number.value)

    """
    # save function name and argument names
    name = func.__name__
    varnames = func.__code__.co_varnames[1:]

    def wrapped(*args):
        # compute initial value
        computed_value = func(*args)

        # create function that updates the computed value
        def _on_change(*_args):
            computed_value.value = func(*args).value

        # handling of computed states as values of higher states
        _args = args[1:] if func.__code__.co_varnames[0] == "self" else args

        # validate arguments are states
        for _arg in _args:
            assert issubclass(
                type(_arg), State
            ), f"Variable {_arg} of computed state {func.__name__} is not a state"

        # register callback on depending state
        for _arg in _args:
            _arg.on_change(_on_change)

        # return computed value
        return computed_value

    return wrapped


class SequenceState(HigherState):
    """
    A sequence state is a utility state to handle lists of basic states.

    It enables iteration, access by index and other utility functions.
    """

    def __init__(self, values: List[BasicState], labels: List[str]):
        super().__init__()
        """
        Initialize a sequence state.

        Parameters
        ----------
        values: list of basic state
            basic states of this sequence
        labels: list of str
            labels or names of the basic states
        """

        assert len(values) == len(
            labels
        ), f"Number of value does not equal number of labels {len(values)}!={len(labels)}"

        self._labels = labels

        for value, label in zip(values, self._labels):
            setattr(self, label, value)

    def __getitem__(self, i: int):
        return self.__getattribute__(self._labels[i])

    def __iter__(self):
        return iter(map(lambda label: self.__getattribute__(label), self._labels))

    def __len__(self):
        return len(self._labels)

    def values(self) -> List[Any]:
        """
        Get the values of all internal states as a list.
        """
        return [attr.value for attr in self]

    def set(self, *args):
        """
        Reassign all internal basic state values and only
        trigger a notification afterwards.
        """
        assert len(args) == len(self)

        with self:
            for i, arg in enumerate(args):
                self[i].value = arg
