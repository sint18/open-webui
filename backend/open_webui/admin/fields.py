# backend/open_webui/admin/fields.py
from dataclasses import dataclass
from datetime import datetime, timezone

from markupsafe import Markup
from requests import Request
from starlette.datastructures import FormData
from starlette_admin import fields

@dataclass
class EpochDateTimeField(fields.DateTimeField):
    """
    DB stores epoch seconds (or ms). Forms show a datetime picker.
    - display: epoch -> formatted datetime (uses DateTimeField's template)
    - form submit: datetime -> epoch seconds (int)
    """
    def __init__(self, name: str, *, assume_tz: str = "UTC", **kwargs):
        # you can still pass DateTimeField kwargs like label=..., read_only=..., format=...
        super().__init__(name, **kwargs)
        self.assume_tz = assume_tz  # "UTC" or "local"

    def _to_dt(self, v):
        if v in (None, ""):
            return None
        if isinstance(v, datetime):
            return v if v.tzinfo else v.replace(tzinfo=timezone.utc)
        # int/str epoch; tolerate ms
        ts = int(v)
        if ts > 10_000_000_000:  # ms -> s
            ts //= 1000
        return datetime.fromtimestamp(ts, tz=timezone.utc)

    async def parse_obj(self, request, obj):
        # value used to prefill form input
        return self._to_dt(getattr(obj, self.name, None))

    async def serialize_value(self, request, value, action):
        # value shown in list/detail; delegate to DateTimeField after converting
        dt = self._to_dt(value)
        return await super().serialize_value(request, dt, action)

    async def parse_form_data(self, request: Request, form_data: FormData, action):
        """
        HTML <input type="datetime-local"> posts a naive ISO string (no tz).
        Treat it as UTC by default, or as local time if assume_tz='local'.
        """
        raw = form_data.get(self.name)
        if raw in (None, ""):
            return None
        # raw like 'YYYY-MM-DDTHH:MM' or 'YYYY-MM-DDTHH:MM:SS'
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            # fallback if seconds missing
            dt = datetime.strptime(raw, "%Y-%m-%dT%H:%M")
        if self.assume_tz.lower() == "local":
            return int(dt.timestamp())
        else:
            return int(dt.replace(tzinfo=timezone.utc).timestamp())

@dataclass
class Base64ImageField(fields.ImageField):
    def __init__(self, name: str, *, mime: str = "image/jpeg", height: int = 64, **kwargs):
        # read_only default True unless overridden
        kwargs.setdefault("read_only", True)
        super().__init__(name, **kwargs)
        self.mime = mime
        self.height = height

    async def serialize_value(self, request, value, action):
        if not value:
            return ""
        src = value if str(value).startswith("data:") else f"data:{self.mime};base64,{value}"
        return f'<img src="{src}" alt="avatar" style="height:{self.height}px;width:{self.height}px;object-fit:cover;border-radius:50%;" />'

