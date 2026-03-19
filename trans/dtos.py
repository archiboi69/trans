from __future__ import annotations

from enum import Enum

from pydantic import BaseModel, ConfigDict, Field


class TransBaseModel(BaseModel):
    model_config = ConfigDict(populate_by_name=True, extra="ignore")


class TransTokenResponse(TransBaseModel):
    access_token: str
    token_type: str
    expires_in: int
    refresh_token: str
    scope: str | None = None


class TransErrorResponse(TransBaseModel):
    error: str
    error_description: str | None = None


class TransPaymentCurrency(str, Enum):
    EUR = "eur"
    ALL = "all"
    BAM = "bam"
    BGN = "bgn"
    CZK = "czk"
    GBP = "gbp"
    HUF = "huf"
    ISK = "isk"
    KZT = "kzt"
    KGS = "kgs"
    MKD = "mkd"
    MDL = "mdl"
    PLN = "pln"
    RON = "ron"
    RUB = "rub"
    RSD = "rsd"
    SEK = "sek"
    CHF = "chf"
    TRY = "try"
    UAH = "uah"
    BYN = "byn"


class TransVehicleSizeEnum(str, Enum):
    ANY_SIZE = "any_size"
    BUS = "bus"
    BUS_DOUBLE_TRAILER = "bus_double_trailer"
    BUS_DOUBLE_TRAILER_LORRY = "bus_double_trailer_lorry"
    BUS_DOUBLE_TRAILER_SOLO = "bus_double_trailer_solo"
    BUS_LORRY = "bus_lorry"
    BUS_LORRY_SOLO = "bus_lorry_solo"
    BUS_SOLO = "bus_solo"
    DOUBLE_TRAILER = "double_trailer"
    DOUBLE_TRAILER_LORRY = "double_trailer_lorry"
    DOUBLE_TRAILER_LORRY_SOLO = "double_trailer_lorry_solo"
    DOUBLE_TRAILER_SOLO = "double_trailer_solo"
    LORRY = "lorry"
    LORRY_SOLO = "lorry_solo"
    SOLO = "solo"


class TransVehicleBodyEnum(str, Enum):
    ALUMINUM = "aluminum"
    BDE = "bde"
    BOX = "box"
    CAR_TRANSPORTER = "car-transporter"
    CHEMICAL_TANKER = "chemical-tanker"
    COILMULDE = "coilmulde"
    COOLER = "cooler"
    CURTAINSIDER = "curtainsider"
    DUMP_TRUCK = "dump-truck"
    FOOD_TANKER = "food-tanker"
    GAS_TANKER = "gas-tanker"
    HOOK_TRUCK = "hook-truck"
    ISOTHERM = "isotherm"
    JOLODA = "joloda"
    JUMBO = "jumbo"
    LOG_TRAILER = "log-trailer"
    LOW_LOADER = "low-loader"
    MEATHANGING = "meathanging"
    MEGA = "mega"
    OPEN_BOX = "open-box"
    OTHER = "other"
    PETROLEUM_TANKER = "petroleum-tanker"
    PLATFORM_TRAILER = "platform-trailer"
    SILOS = "silos"
    STANDARD_20 = "20-standard"
    STANDARD_40 = "40-standard"
    STANDARD_45 = "45-standard"
    STANDARD_TENT = "standard-tent"
    STEEL = "steel"
    SWAP_BODY_SYSTEM = "swap-body-system"
    TANK_BODY_20 = "tank-body-20"
    TANK_BODY_40 = "tank-body-40"
    TANKER = "tanker"
    TRUCK = "truck"
    WALKINGFLOOR = "walkingfloor"


class TransMonitoringEnum(str, Enum):
    WITHOUT_MONITORING = "without_monitoring"
    EXPECTED = "expected"
    REQUIRED = "required"


class TransOtherRequirement(str, Enum):
    A_SIGN = "a-sign"
    ABP_CAT_1_PERMIT = "abp_cat_1_permit"
    ABP_CAT_2_PERMIT = "abp_cat_2_permit"
    ABP_CAT_3_PERMIT = "abp_cat_3_permit"
    ADR = "adr"
    AUTORISATION_ECMT_CEMT_LICENCE = "autorisation_ecmt_cemt_licence"
    BACKUP_GENERATOR_FOR_REEFER = "backup_generator_for_reefer"
    CARNET_ATA = "carnet_ata"
    CARNET_TIR = "carnet_tir"
    CLEANING_CERTIFICATE = "cleaning_certificate"
    CORNER_PROTECTOR = "corner_protector"
    CUSTOM_ROPE = "custom_rope"
    DOUBLE_CAST = "double_cast"
    DOPPEL_DECKER = "doppel_decker"
    GMP_CERTIFICATE = "gmp_certificate"
    GOODS_TO_DECLARE = "goods_to_declare"
    GPS = "gps"
    HDS = "hds"
    LIFT = "lift"
    LOAD_SECURING_POLES = "load_securing_poles"
    MULTI_TEMPERATURE = "multi_temperature"
    NON_SLIP_MATS = "non-slip_mats"
    PALLET_BASKET = "pallet_basket"
    QUALIMAT_CERTIFICATE = "qualimat_certificate"
    RAMP_HEIGHT = "ramp_height"
    SAFETY_BAR = "safety_bar"
    TEMPERATURE_LOG = "temperature_log"
    THERMOMETER = "thermometer"
    TRANSPORT_LINES = "transport_lines"
    WASTE_TRANSPORT_ITALY_LICENCE = "waste_transport_italy_licence"
    XL_CERTIFICATE = "xl_certificate"


class TransRequiredAdrClass(str, Enum):
    ADR_1 = "adr_1"
    ADR_1_1 = "adr_1_1"
    ADR_1_2 = "adr_1_2"
    ADR_1_3 = "adr_1_3"
    ADR_1_4 = "adr_1_4"
    ADR_1_5 = "adr_1_5"
    ADR_1_6 = "adr_1_6"
    ADR_2 = "adr_2"
    ADR_2_1 = "adr_2_1"
    ADR_2_2 = "adr_2_2"
    ADR_2_3 = "adr_2_3"
    ADR_3 = "adr_3"
    ADR_4_1 = "adr_4_1"
    ADR_4_2 = "adr_4_2"
    ADR_4_3 = "adr_4_3"
    ADR_5_1 = "adr_5_1"
    ADR_5_2 = "adr_5_2"
    ADR_6_1 = "adr_6_1"
    ADR_6_2 = "adr_6_2"
    ADR_7 = "adr_7"
    ADR_8 = "adr_8"
    ADR_9 = "adr_9"


class TransRequiredWayOfLoading(str, Enum):
    BACK = "back"
    SIDE = "side"
    TOP = "top"


class TransRequiredDoorType(str, Enum):
    TAILGATE = "tailgate"
    DOOR = "door"


class TransRequiredTipperTrailerAdditionalEquipment(str, Enum):
    SINGLE_GRAIN_HATCH = "single_grain_hatch"
    DOUBLE_GRAIN_HATCH = "double_grain_hatch"
    DUST_SOCK = "dust_sock"


class TransOperationType(str, Enum):
    LOADING = "loading"
    UNLOADING = "unloading"


class TransTransportTypeEnum(str, Enum):
    FTL = "ftl"
    LTL = "ltl"
    MULTI_FTL = "multi_ftl"


class TransTransportScheduleType(str, Enum):
    SHIPPER = "shipper"
    CARRIER = "carrier"
    TOGETHER = "together"


class TransTransportSettlement(str, Enum):
    ROUTE = "route"
    TON = "ton"


class TransTransportSettlementBasis(str, Enum):
    LOADING = "loading"
    UNLOADING = "unloading"


class TransPaymentPeriodEnum(str, Enum):
    DEFERRED = "deferred"
    PAYMENT_IN_ADVANCE = "payment_in_advance"
    PAYMENT_ON_UNLOADING = "payment_on_unloading"


class TransTransport(TransBaseModel):
    type: TransTransportTypeEnum | None = None
    count: float | None = None
    schedule_type: TransTransportScheduleType | None = None
    settlement: TransTransportSettlement | None = None
    settlement_basis: TransTransportSettlementBasis | None = None
    total_weight: float | None = None
    units_per_transport: float | None = None


class TransTemperature(TransBaseModel):
    min: float | None = None
    max: float | None = None


class TransRequirements(TransBaseModel):
    """OpenAPI spec misspells "monitoring" as "monitorig"."""

    transport: TransTransport | None = None
    vehicle_size: TransVehicleSizeEnum | None = None
    is_ftl: bool
    required_truck_bodies: list[TransVehicleBodyEnum]
    other_requirements: list[TransOtherRequirement] | None = None
    required_adr_classes: list[TransRequiredAdrClass] | None = None
    required_ways_of_loading: list[TransRequiredWayOfLoading] | None = None
    required_door_types: list[TransRequiredDoorType] | None = None
    required_tipper_trailer_additional_equipment: (
        list[TransRequiredTipperTrailerAdditionalEquipment] | None
    ) = None
    # Intentionally misspelled to match the Trans payload key.
    monitorig: TransMonitoringEnum | None = None
    temperature: TransTemperature | None = None
    shipping_remarks: str | None = None


class TransPaymentPeriod(TransBaseModel):
    payment: TransPaymentPeriodEnum | None = None
    days: int | None = None


class TransPaymentPrice(TransBaseModel):
    value: float | None = None
    currency: TransPaymentCurrency | None = None


class TransPayment(TransBaseModel):
    price: TransPaymentPrice | None = None
    period: TransPaymentPeriod | None = None


class TransAddress(TransBaseModel):
    country: str
    street: str | None = None
    number: str | None = None
    locality: str
    postal_code: str
    description: str | None = None


class TransCoordinates(TransBaseModel):
    latitude: float | None = None
    longitude: float | None = None


class TransPlace(TransBaseModel):
    address: TransAddress
    coordinates: TransCoordinates | None = None


class TransTimespans(TransBaseModel):
    end: str
    begin: str
    begin_local: str | None = None
    end_local: str | None = None
    timezone: str | None = None


class TransOperation(TransBaseModel):
    operation_order: int
    operation_time: int | None = None
    loads: list[str] | None = None
    timespans: TransTimespans
    type: TransOperationType


class TransSpot(TransBaseModel):
    name: str | None = None
    description: str | None = None
    spot_order: int
    place: TransPlace
    operations: list[TransOperation] = Field(min_length=1)


class TransCarrier(TransBaseModel):
    company_id: int | None = None


class TransFreightExchangeRequest(TransBaseModel):
    send_order_proposal_automatically: bool | None = None
    exchange_recipients: str | None = None
    external_source: str | None = None
    # Docs describe this as "freight capacity in tonnes"; allow fractional tonnes.
    capacity: float
    loading_meters: float | None = None
    requirements: TransRequirements
    publish_date: str | None = None
    decision_date: str | None = None
    payment: TransPayment | None = None
    publish: bool
    # Must be present even if empty.
    loads: list[str] = Field(default_factory=list)
    spots: list[TransSpot]
    carriers: list[TransCarrier] | None = None
    contact_employees: list[str] | None = None
    callback_url: str | None = None
    transit_time: float | None = None


class TransContactEmployee(TransBaseModel):
    last_name: str | None = None
    name: str | None = None
    trans_id: str | None = None


class TransLoadItem(TransBaseModel):
    amount: int | None = None
    description: str | None = None
    height: int | None = None
    id: int | None = None
    is_exchangeable: bool | None = None
    is_stackable: bool | None = None
    length: int | None = None
    load_id: str | None = None
    name: str | None = None
    type_of_load: str | None = None
    volume: int | None = None
    weight: int | None = None
    width: int | None = None


class TransPrice(TransBaseModel):
    value: float | None = None
    currency: TransPaymentCurrency | None = None


class TransResponseRequirements(TransBaseModel):
    exemption_from_adr: bool | None = None
    is_ftl: bool | None = None
    monitoring: TransMonitoringEnum | None = None
    other_requirements: list[TransOtherRequirement] | None = None
    required_adr_classes: list[TransRequiredAdrClass] | None = None
    required_door_types: list[TransRequiredDoorType] | None = None
    required_tipper_trailer_additional_equipment: (
        list[TransRequiredTipperTrailerAdditionalEquipment] | None
    ) = None
    required_truck_bodies: list[TransVehicleBodyEnum] | None = None
    required_ways_of_loading: list[TransRequiredWayOfLoading] | None = None
    shipping_remarks: str | None = None
    temperature: TransTemperature | None = None
    transport: TransTransport | None = None
    vehicle_size: TransVehicleSizeEnum | None = None


class TransFreightExchangeResponse(TransBaseModel):
    accepted_price: TransPrice | None = None
    capacity: float | None = None
    carrier: dict | None = None
    contact_employees: list[TransContactEmployee] | None = None
    transit_time: int | None = None
    distance: float | None = None
    end_reason: str | None = None
    height: float | None = None
    id: int | None = None
    is_first_buy: bool | None = None
    length: float | None = None
    loading_meters: float | None = None
    loads: list[TransLoadItem] | None = None
    publication_price: TransPrice | None = None
    publication_status: str | None = None
    reference_number: str | None = None
    requirements: TransResponseRequirements | None = None
    shipment_external_id: str | None = None
    spots: list[TransSpot] | None = None
    status: str | None = None
    surcharges: list[dict] | dict | None = None
    volume: float | None = None
    width: float | None = None
