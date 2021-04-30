class MetaConstants:

    BASE_EXPORT_DIR = 'exported_data'

    class IEXDataFields:
        date = 'date'
        minute = 'minute'
        label = 'label'
        high = 'high'
        low = 'low'
        average = 'average'
        volume = 'volume'
        notional = 'notional'
        numberOfTrades = 'numberOfTrades'
        marketHigh = 'marketHigh'
        marketLow = 'marketLow'
        marketAverage = 'marketAverage'
        marketVolume = 'marketVolume'
        marketNotional = 'marketNotional'
        marketNumberOfTrades = 'marketNumberOfTrades'
        open = 'open'
        close = 'close'
        marketOpen = 'marketOpen'
        marketClose = 'marketClose'
        changeOverTime = 'changeOverTime'
        marketChangeOverTime = 'marketChangeOverTime'


class ScraperConstants:

    OUTPUT_DIR = f'{MetaConstants.BASE_EXPORT_DIR}/raw'

    class Config:
        API_TOKEN = 'api_token'
        API_SECRET = 'api_secret'
        SANDBOX_MODE = 'sandbox'

    class Stage:
        SANDBOX = 'sandbox'
        STABLE = 'stable'

    class SortMethods:
        ASC = 'asc'
        DESC = 'desc'


class DatasetConstants:

    OUTPUT_DIR = f'{MetaConstants.BASE_EXPORT_DIR}/datasets'
    META_FILENAME = 'meta-as-fuck.json'

