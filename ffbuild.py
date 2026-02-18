from abc import ABC
from collections.abc import Iterable, Iterator, Mapping
from types import NotImplementedType
from typing import (
    Final,
    NoReturn,
    NotRequired,
    TypedDict,
    Unpack,
    final,
    overload,
    override,
)


SPECIAL_CHARS: Final[frozenset[str]] = frozenset(('[', ']', '=', ';', ','))


@final
class Value:
    @override
    def __init__(self, value: int | str) -> None:
        if isinstance(value, int):
            value = str(value)
        self.text: str = value

    @override
    def __hash__(self) -> int:
        return hash(self.text)

    @override
    def __eq__(self, value: object, /) -> bool | NotImplementedType:
        if isinstance(value, Value):
            return self.text == value.text
        return NotImplemented

    @override
    def __ne__(self, value: object, /) -> bool | NotImplementedType:
        if isinstance(value, Value):
            return self.text != value.text
        return NotImplemented

    @override
    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.text!r})'

    @override
    def __str__(self) -> str:
        value = self.text
        if self.contains_special_chars:
            value = value.replace('\\', '\\\\')
            for char in SPECIAL_CHARS:
                value = value.replace(char, f'\\{char}')
        return value

    @property
    def contains_special_chars(self) -> bool:
        return not SPECIAL_CHARS.isdisjoint(self.text)


class Argument(ABC):
    @override
    def __init__(self, value: Value | int | str) -> None:
        if isinstance(value, (int, str)):
            value = Value(value)
        self.value: Final[Value] = value


@final
class PositionalArgument(Argument):
    @override
    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.value!r})'

    @override
    def __str__(self) -> str:
        return str(self.value)


@final
class KeyArgument(Argument):
    @override
    def __init__(self, key: str, value: Value | int | str) -> None:
        super().__init__(value)
        self.key = key

    @override
    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.key!r}, {self.value!r})'

    @override
    def __str__(self) -> str:
        return f'{self.key}={self.value}'


class _Kwargs(TypedDict):
    argument: NotRequired[Arguments | Argument]
    key: NotRequired[str]
    value: NotRequired[Value | int | str]


class Arguments:
    @override
    def __init__(
        self,
        *args: Arguments | Argument | Value | int | str,
        **kwargs: Value | int | str,
    ) -> None:
        self._all: Final[list[Argument]] = []
        for arg in args:
            if isinstance(arg, Arguments):
                self.extend(arg)
            else:
                self.append(arg)
        for key, value in kwargs.items():
            self.append(key, value)

    def __bool__(self) -> bool:
        return bool(self._all)

    def __iter__(self) -> Iterator[Argument]:
        return iter(self._all)

    @override
    def __repr__(self) -> str:
        return f'{type(self).__name__}({", ".join(map(repr, self._all))})'

    @override
    def __str__(self) -> str:
        text = ':'.join(map(str, self))
        if self.requires_quotes:
            text = f"'{text}'"
        return text

    @property
    def requires_quotes(self) -> bool:
        return any(arg.value.contains_special_chars for arg in self)

    @overload
    def append(self, argument: Argument) -> None: ...

    @overload
    def append(self, value: Value | int | str) -> None: ...

    @overload
    def append(self, key: str, value: Value | int | str) -> None: ...

    def append(  # pyright: ignore[reportInconsistentOverload]
        self,
        *args: Argument | Value | int | str,
        **kwargs: Unpack[_Kwargs],
    ) -> None:
        # fmt: off
        match (args, kwargs):
            case (
                ([Argument() as arg], {}) |
                ([], {'argument': Argument() as arg})
            ):
                pass

            case (
                ([Value() | int() | str() as value,], {}) |
                ([], {'value': Value() | int() | str() as value})
            ):
                arg = PositionalArgument(value)

            case (
                ([str() as key, Value() | int() | str() as value], {}) |
                ([str() as key], {'value': Value() | int() | str() as value}) |
                ([Value() | int() | str() as value], {'key': str() as key}) |
                (
                    [],
                    {
                        'key': str() as key,
                        'value': Value() | int() | str() as value
                    }
                )
            ):
                arg = KeyArgument(key, value)

            case _:
                raise ValueError(f'invalid args {args!r} and kwargs {kwargs!r}')
        # fmt: on
        self._all.append(arg)

    def extend(self, args: Iterable[Argument]) -> None:
        for arg in args:
            self.append(arg)


@final
class Link:
    def __init__(self, name: str) -> None:
        self.name = name

    @override
    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.name!r})'

    @override
    def __str__(self) -> str:
        return f'[{self.name}]'


@final
class Links:
    @override
    def __init__(self, links: Iterable[Link] = ()) -> None:
        self._all: Final[list[Link]] = list(links)

    def __iter__(self) -> Iterator[Link]:
        return iter(self._all)

    @override
    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._all!r})'

    @override
    def __str__(self) -> str:
        return ''.join(map(str, self))

    def append(self, link: Link | str) -> Link:
        if isinstance(link, str):
            link = Link(link)
        self._all.append(link)
        return link


def _prepare_links(
    links: Links | Iterable[Link | str] | Link | str | None,
) -> Links:
    match links:
        case Links():
            return links
        case Link() as link:
            return Links((link,))
        case str() as name:
            return Links((Link(name),))
        case None:
            return Links()
        case _:
            return Links(
                Link(link) if isinstance(link, str) else link for link in links
            )


@final
class Filter:
    @override
    def __init__(
        self,
        name: str,
        *args: Arguments | Argument | Value | int | str,
        kwargs: Mapping[str, Value | int | str] | None = None,
        input: Links | Iterable[Link | str] | Link | str | None = None,
        output: Links | Iterable[Link | str] | Link | str | None = None,
        **override_kwargs: Value | int | str,
    ) -> None:
        self.name = name
        kwargs = {} if kwargs is None else dict(kwargs)
        kwargs.update(override_kwargs)
        self.arguments = Arguments(*args, **kwargs)
        self.input: Final = _prepare_links(input)
        self.output: Final = _prepare_links(output)

    @override
    def __repr__(self) -> str:
        return f'{type(self).__name__}({self.name!r}, {self.arguments!r}, input={self.input!r}, output={self.output!r})'

    @override
    def __str__(self) -> str:
        frags = [str(self.input), self.name]
        if self.arguments:
            frags.append('=')
            frags.append(str(self.arguments))
        frags.append(str(self.output))
        return ''.join(frags)


@final
class FilterChain:
    @override
    def __init__(self, filters: Iterable[Filter] | None = None) -> None:
        if filters is None:
            filters = []
        else:
            filters = list(filters)

        self._filters: Final[list[Filter]] = filters

    def __bool__(self) -> bool:
        return bool(self._filters)

    def __iter__(self) -> Iterator[Filter]:
        return iter(self._filters)

    @override
    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._filters!r})'

    @override
    def __str__(self) -> str:
        return ','.join(map(str, self._filters))


@final
class FilterGraph:
    @override
    def __init__(self, chains: Iterable[FilterChain] | None = None) -> None:
        if chains is None:
            chains = []
        else:
            chains = list(chains)

        self._chains: Final[list[FilterChain]] = chains

    def __bool__(self) -> bool:
        return bool(self._chains)

    def __iter__(self) -> Iterator[FilterChain]:
        return iter(self._chains)

    @override
    def __repr__(self) -> str:
        return f'{type(self).__name__}({self._chains!r})'

    @override
    def __str__(self) -> str:
        return ';'.join(map(str, self))

    @overload
    def append(self, chain: FilterChain | None = None) -> FilterChain: ...

    @overload
    def append(self, filter: Filter, /, *filters: Filter) -> FilterChain: ...

    def append(
        self,
        *args: FilterChain | Filter | None,
        **kwargs: FilterChain | None,
    ) -> FilterChain:
        def error() -> NoReturn:
            raise ValueError(f'invalid args {args!r} and kwargs {kwargs!r}')

        if 'chain' in kwargs:
            chain = kwargs.pop('chain')
            if args or kwargs:
                error()
            if chain is None:
                chain = FilterChain()
            self._chains.append(chain)
            return chain

        if kwargs:
            error()

        filters: list[Filter] = []

        for arg in args:
            if not isinstance(arg, Filter):
                error()
            filters.append(arg)

        chain = FilterChain(filters=filters)
        self._chains.append(chain)
        return chain

    def append_filter(
        self,
        name: str,
        *args: Arguments | Argument | Value | int | str,
        kwargs: Mapping[str, Value | int | str] | None = None,
        input: Links | Iterable[Link | str] | Link | str | None = None,
        output: Links | Iterable[Link | str] | Link | str | None = None,
        **override_kwargs: Value | int | str,
    ) -> FilterChain:
        return self.append(
            Filter(
                name,
                *args,
                kwargs=kwargs,
                input=input,
                output=output,
                **override_kwargs,
            )
        )
