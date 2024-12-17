from dataclasses import dataclass

import screeninfo


@dataclass
class Geometry:
    width: int
    height: int
    x: int
    y: int

    @classmethod
    def from_str(cls, geometry_str: str):
        _split = geometry_str.split("+")
        width, height = map(int, _split[0].split("x"))
        x, y = map(int, _split[1:])
        return cls(width=width, height=height, x=x, y=y)

    def __str__(self):
        return f"{self.width}x{self.height}+{self.x}+{self.y}"


def get_active_monitor(geometry: str | Geometry) -> screeninfo.common.Monitor:
    geometry = Geometry.from_str(geometry) if isinstance(geometry, str) else geometry

    for monitor in screeninfo.get_monitors():
        if monitor.x <= geometry.x < monitor.x + monitor.width:
            return monitor
    return screeninfo.get_monitors()[0]
