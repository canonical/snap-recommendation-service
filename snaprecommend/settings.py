from snaprecommend import db
from snaprecommend.models import Settings


def get_settings():
    return db.session.query(Settings).all()


def get_setting(key: str) -> Settings | None:
    return db.session.query(Settings).filter(Settings.key == key).first()


def get_settings_by_keys(keys: list[str]) -> dict[str, Settings | None]:
    rows = db.session.query(Settings).filter(Settings.key.in_(keys)).all()
    by_key = {row.key: row for row in rows}
    return {key: by_key.get(key) for key in keys}


def set_setting(key: str, value) -> Settings:
    setting = get_setting(key)
    if setting:
        setting.value = value
    else:
        setting = Settings(key=key, value=value)
    db.session.add(setting)
    db.session.commit()
    return setting
