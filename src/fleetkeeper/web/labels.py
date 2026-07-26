"""Romanian labels for the fixed choices a vehicle is described with.

These four sets are the only places the interface offers a list rather than a free text box,
because the catalogue reasons about them. Everything else about a car — make, model, part
numbers, workshops — is typed freely, since no list anyone could write would stay complete.

Each entry may carry a note. Whether a car has a timing belt or a timing chain decides
whether it ever gets a distribution reminder, and most owners have no idea which they have,
so the note says where to look.
"""

from dataclasses import dataclass

from fleetkeeper.models.enums import Drivetrain, Equipment, FuelType, GearboxType


@dataclass(frozen=True, slots=True)
class Choice:
    value: str
    label: str
    note: str | None = None


FUEL_TYPES = (
    Choice(FuelType.PETROL, "Benzină"),
    Choice(FuelType.DIESEL, "Diesel"),
    Choice(FuelType.PETROL_LPG, "Benzină și GPL"),
    Choice(FuelType.HYBRID_PETROL, "Hibrid pe benzină", "Motor termic plus electric, fără priză"),
    Choice(FuelType.HYBRID_DIESEL, "Hibrid pe diesel", "Motor termic plus electric, fără priză"),
    Choice(FuelType.PLUGIN_HYBRID, "Hibrid cu priză", "Se încarcă de la priză și merge electric"),
    Choice(FuelType.ELECTRIC, "Electric"),
)

GEARBOX_TYPES = (
    Choice(GearboxType.MANUAL, "Manuală"),
    Choice(
        GearboxType.TORQUE_CONVERTER,
        "Automată clasică",
        "Cu convertizor hidraulic. Cutiile ZF sau Aisin din BMW, Audi, Mercedes",
    ),
    Choice(
        GearboxType.DUAL_CLUTCH_DRY,
        "Automată cu ambreiaj dublu, uscat",
        "DSG cu 7 trepte la Volkswagen, Audi, Seat, Škoda, pe motoare mai mici",
    ),
    Choice(
        GearboxType.DUAL_CLUTCH_WET,
        "Automată cu ambreiaj dublu, umed",
        "DSG cu 6 trepte, sau 7 trepte pe motoare puternice",
    ),
    Choice(GearboxType.CVT, "Automată cu variație continuă", "CVT, fără trepte propriu-zise"),
)

DRIVETRAINS = (
    Choice(Drivetrain.FRONT, "Față"),
    Choice(Drivetrain.REAR, "Spate"),
    Choice(Drivetrain.ALL, "Integrală", "4x4, quattro, xDrive, 4MOTION și altele"),
)

EQUIPMENT = (
    Choice(
        Equipment.TIMING_BELT,
        "Curea de distribuție",
        "Bifează doar dacă are curea, nu lanț. Scrie în manual sau întreabă la service; "
        "de asta depinde cea mai scumpă lucrare din listă",
    ),
    Choice(
        Equipment.PARTICULATE_FILTER,
        "Filtru de particule",
        "Aproape toate motoarele diesel de după 2009 și benzinele de după 2018",
    ),
    Choice(Equipment.ADBLUE, "Rezervor AdBlue", "Diesel de după 2015, cu rezervor separat"),
    Choice(Equipment.LPG_SYSTEM, "Instalație GPL"),
    Choice(
        Equipment.AIR_SUSPENSION,
        "Suspensie pneumatică",
        "Mașina se ridică și se coboară singură, pe perne de aer",
    ),
    Choice(Equipment.AIR_CONDITIONING, "Aer condiționat sau climatronic"),
)

FUEL_LABELS = {choice.value: choice.label for choice in FUEL_TYPES}
GEARBOX_LABELS = {choice.value: choice.label for choice in GEARBOX_TYPES}
DRIVETRAIN_LABELS = {choice.value: choice.label for choice in DRIVETRAINS}
EQUIPMENT_LABELS = {choice.value: choice.label for choice in EQUIPMENT}

SECTION_LABELS = {
    "documents": "Documente și obligații legale",
    "engine": "Motor și fluide",
    "transmission": "Transmisie",
    "running_gear": "Frânare și rulare",
    "electrical": "Electrice și confort",
    "other": "Diverse",
}

INTERVAL_SOURCE_LABELS = {
    "manufacturer": "interval de la producător",
    "practice": "convenție de atelier",
    "estimate": "estimare, se verifică",
}
