from snaprecommend import db
from snaprecommend.models import Settings


def get_settings():
    return db.session.query(Settings).all()


def get_setting(key: str) -> Settings | None:
    return db.session.query(Settings).filter(Settings.key == key).first()


def set_setting(key: str, value) -> Settings:
    setting = get_setting(key)
    if setting:
        setting.value = value
    else:
        setting = Settings(key=key, value=value)
    db.session.add(setting)
    db.session.commit()
    return setting
