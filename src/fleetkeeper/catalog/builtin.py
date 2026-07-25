"""The built-in service catalogue, in Romanian, as the interface presents it.

Intervals are manufacturer guidance for the VAG engines this was written for, rounded to
the values a workshop would actually quote. They are defaults, not rules: every one of
them can be shortened, lengthened or switched off per vehicle once a car is added.

Where an interval is deliberately absent the item is wear-driven rather than scheduled —
a clutch or a wheel bearing is replaced when it fails, and pretending otherwise would
produce reminders nobody should act on.
"""

from dataclasses import dataclass, field

from fleetkeeper.models.enums import (
    CategoryKind,
    CategorySection,
    Drivetrain,
    Equipment,
    FuelType,
    GearboxType,
)

PETROL_ENGINES = (
    FuelType.PETROL,
    FuelType.PETROL_LPG,
    FuelType.HYBRID_PETROL,
    FuelType.PLUGIN_HYBRID,
)
DIESEL_ENGINES = (FuelType.DIESEL, FuelType.HYBRID_DIESEL)
# Anything that burns fuel. Used by items a fully electric car has no equivalent of: no
# engine oil, no accessory belt, no starter motor.
COMBUSTION_ENGINES = PETROL_ENGINES + DIESEL_ENGINES
DUAL_CLUTCH = (GearboxType.DUAL_CLUTCH_DRY, GearboxType.DUAL_CLUTCH_WET)


@dataclass(frozen=True, slots=True)
class CategoryDefinition:
    code: str
    name: str
    section: CategorySection
    kind: CategoryKind = CategoryKind.MAINTENANCE
    interval_km: int | None = None
    interval_months: int | None = None
    fuel_types: tuple[FuelType, ...] = ()
    gearbox_types: tuple[GearboxType, ...] = ()
    drivetrains: tuple[Drivetrain, ...] = ()
    equipment: tuple[Equipment, ...] = ()
    hint: str | None = field(default=None)


DOCUMENTS = (
    CategoryDefinition(
        code="rca",
        name="Asigurare RCA",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="Obligatorie. Se poate încheia pe 1, 6 sau 12 luni, iar data de expirare este cea trecută pe poliță.",
    ),
    CategoryDefinition(
        code="itp",
        name="Inspecție tehnică periodică (ITP)",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="La autoturisme, de regulă la 2 ani, iar după 12 ani de la prima înmatriculare, anual. Data exactă este pe fișa ITP.",
    ),
    CategoryDefinition(
        code="rovinieta",
        name="Rovinietă",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="Obligatorie pe drumurile naționale și autostrăzi. Amenda se dă chiar dacă ai depășit termenul cu o zi.",
    ),
    CategoryDefinition(
        code="casco",
        name="Asigurare CASCO",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="Opțională.",
    ),
    CategoryDefinition(
        code="vigneta_externa",
        name="Vinietă pentru străinătate",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="Ungaria, Austria, Slovacia și altele. Se cumpără înainte de a intra pe drumul cu taxă, nu după.",
    ),
    CategoryDefinition(
        code="verificare_gpl",
        name="Verificare instalație GPL",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        equipment=(Equipment.LPG_SYSTEM,),
        hint="Verificare periodică obligatorie. Fără ea, ITP-ul nu se poate obține.",
    ),
    CategoryDefinition(
        code="extinctor",
        name="Extinctor",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="Are data de expirare inscripționată pe corp. Se verifică la ITP.",
    ),
    CategoryDefinition(
        code="kit_prim_ajutor",
        name="Kit de prim ajutor",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="Expiră, la fel ca medicamentele din el.",
    ),
)

ENGINE = (
    CategoryDefinition(
        code="ulei_motor",
        name="Ulei de motor și filtru de ulei",
        section=CategorySection.ENGINE,
        interval_km=15_000,
        interval_months=12,
        fuel_types=COMBUSTION_ENGINES,
        hint="Intervalul producătorului presupune condiții ideale. La diesel cu filtru de particule și drumuri scurte în oraș, 10.000 km este mai sigur.",
    ),
    CategoryDefinition(
        code="filtru_aer",
        name="Filtru de aer",
        section=CategorySection.ENGINE,
        interval_km=30_000,
        interval_months=24,
        fuel_types=COMBUSTION_ENGINES,
    ),
    CategoryDefinition(
        code="filtru_habitaclu",
        name="Filtru de habitaclu (polen)",
        section=CategorySection.ENGINE,
        interval_km=15_000,
        interval_months=12,
        hint="Când se înfundă, geamurile se dezaburesc greu și apare miros de umezeală la pornirea ventilației.",
    ),
    CategoryDefinition(
        code="filtru_combustibil",
        name="Filtru de combustibil",
        section=CategorySection.ENGINE,
        interval_km=60_000,
        interval_months=48,
        fuel_types=DIESEL_ENGINES,
        hint="La benzină este montat de obicei în rezervor și nu se schimbă periodic.",
    ),
    CategoryDefinition(
        code="bujii",
        name="Bujii",
        section=CategorySection.ENGINE,
        interval_km=60_000,
        interval_months=60,
        fuel_types=PETROL_ENGINES,
        hint="La motoarele supraalimentate (TSI, TFSI) intervalul real este mai scurt, în jur de 30.000-40.000 km.",
    ),
    CategoryDefinition(
        code="bujii_incandescente",
        name="Bujii incandescente",
        section=CategorySection.ENGINE,
        fuel_types=DIESEL_ENGINES,
        hint="Se schimbă la defect, nu periodic. Semnul clar: porniri greoaie pe vreme rece.",
    ),
    CategoryDefinition(
        code="lichid_racire",
        name="Lichid de răcire (antigel)",
        section=CategorySection.ENGINE,
        interval_km=200_000,
        interval_months=60,
        hint="Își pierde proprietățile anticorozive chiar dacă arată curat. Verifică specificația (G12, G13) înainte de completare, tipurile nu se amestecă.",
    ),
    CategoryDefinition(
        code="lichid_frana",
        name="Lichid de frână",
        section=CategorySection.ENGINE,
        interval_months=24,
        hint="Se schimbă după timp, nu după kilometri: absoarbe apă din aer chiar și cu mașina în garaj. Apa fierbe la frânări repetate și pedala se duce în podea exact când ai nevoie de ea.",
    ),
    CategoryDefinition(
        code="curea_distributie",
        name="Curea de distribuție, pompă de apă și role",
        section=CategorySection.ENGINE,
        interval_km=120_000,
        interval_months=72,
        equipment=(Equipment.TIMING_BELT,),
        hint="Cea mai scumpă lucrare amânată din listă: dacă cureaua cedează, motorul se distruge. Se schimbă împreună cu pompa de apă și rolele, fiindcă manopera este aceeași.",
    ),
    CategoryDefinition(
        code="curea_accesorii",
        name="Curea de accesorii",
        section=CategorySection.ENGINE,
        interval_km=90_000,
        interval_months=72,
        fuel_types=COMBUSTION_ENGINES,
        hint="Antrenează alternatorul și pompa de servodirecție. Semn de uzură: fluierat la pornirea la rece.",
    ),
    CategoryDefinition(
        code="adblue",
        name="Completare AdBlue",
        section=CategorySection.ENGINE,
        interval_km=15_000,
        equipment=(Equipment.ADBLUE,),
        hint="Se completează, nu se schimbă. Dacă rezervorul se golește complet, motorul refuză să mai pornească după oprire.",
    ),
    CategoryDefinition(
        code="curatare_dpf",
        name="Curățare filtru de particule (DPF)",
        section=CategorySection.ENGINE,
        interval_km=120_000,
        equipment=(Equipment.PARTICULATE_FILTER,),
        hint="Se colmatează la drumuri exclusiv scurte, fiindcă nu ajunge la temperatura de regenerare. Semne: consum crescut și regenerări tot mai frecvente.",
    ),
    CategoryDefinition(
        code="curatare_egr",
        name="Curățare EGR și clapetă de admisie",
        section=CategorySection.ENGINE,
        interval_km=100_000,
        fuel_types=DIESEL_ENGINES,
        hint="Se cocsează cu funingine, mai ales la mers în oraș. Semne: pierdere de putere și mers neregulat la ralanti.",
    ),
    CategoryDefinition(
        code="injectoare",
        name="Verificare injectoare",
        section=CategorySection.ENGINE,
        interval_km=100_000,
        fuel_types=COMBUSTION_ENGINES,
    ),
    CategoryDefinition(
        code="revizie_generala",
        name="Revizie generală la service",
        section=CategorySection.ENGINE,
        interval_km=15_000,
        interval_months=12,
        hint="Verificarea completă, dincolo de schimbul de ulei: nivele, uzuri, jocuri, erori din calculator.",
    ),
)

TRANSMISSION = (
    CategoryDefinition(
        code="ulei_cutie_manuala",
        name="Ulei cutie manuală",
        section=CategorySection.TRANSMISSION,
        interval_km=120_000,
        gearbox_types=(GearboxType.MANUAL,),
        hint="Producătorul îl declară adesea „pe viață”. La 120.000 km este uzat, iar schimbul este ieftin față de o cutie refăcută.",
    ),
    CategoryDefinition(
        code="ulei_cutie_automata",
        name="Ulei și filtru cutie automată",
        section=CategorySection.TRANSMISSION,
        interval_km=80_000,
        interval_months=96,
        gearbox_types=(GearboxType.TORQUE_CONVERTER,),
        hint="„Lifetime” este marketing, nu inginerie. Cutiile ZF cer schimb la 80.000-100.000 km; altfel apar șocuri la trecerea treptelor și reparația costă de zece ori mai mult.",
    ),
    CategoryDefinition(
        code="ulei_dsg_umed",
        name="Ulei și filtru DSG (ambreiaj umed)",
        section=CategorySection.TRANSMISSION,
        interval_km=60_000,
        interval_months=48,
        gearbox_types=(GearboxType.DUAL_CLUTCH_WET,),
        hint="La DSG-6 cu ambreiaj umed, uleiul lucrează și ca lichid de răcire pentru ambreiaje.",
    ),
    CategoryDefinition(
        code="fluid_mecatronica_dsg",
        name="Fluid mecatronică DSG",
        section=CategorySection.TRANSMISSION,
        interval_km=60_000,
        interval_months=48,
        gearbox_types=(GearboxType.DUAL_CLUTCH_DRY,),
        hint="La DSG-7 uscat, uleiul de cutie este pe viață, dar fluidul hidraulic al mecatronicii nu. Se ratează foarte des, fiindcă lumea aude „pe viață” și se oprește acolo.",
    ),
    CategoryDefinition(
        code="ulei_cvt",
        name="Ulei cutie CVT",
        section=CategorySection.TRANSMISSION,
        interval_km=60_000,
        gearbox_types=(GearboxType.CVT,),
    ),
    CategoryDefinition(
        code="ulei_diferential",
        name="Ulei diferențial",
        section=CategorySection.TRANSMISSION,
        interval_km=120_000,
        drivetrains=(Drivetrain.REAR, Drivetrain.ALL),
        hint="La tracțiune față diferențialul este integrat în cutie și nu are ulei separat.",
    ),
    CategoryDefinition(
        code="ulei_haldex",
        name="Ulei și filtru Haldex",
        section=CategorySection.TRANSMISSION,
        interval_km=60_000,
        drivetrains=(Drivetrain.ALL,),
        hint="Cuplajul de pe puntea spate al sistemelor de tracțiune integrală. Se uită aproape întotdeauna, iar când cedează pompa, tracțiunea integrală dispare fără avertisment.",
    ),
    CategoryDefinition(
        code="kit_ambreiaj",
        name="Kit ambreiaj și volantă",
        section=CategorySection.TRANSMISSION,
        gearbox_types=(GearboxType.MANUAL, *DUAL_CLUTCH),
        hint="Se schimbă la uzură, nu la interval. Semne: patinare la accelerare în treaptă mare, pedală moale, miros de ars la plecări în rampă.",
    ),
)

RUNNING_GEAR = (
    CategoryDefinition(
        code="placute_fata",
        name="Plăcuțe de frână față",
        section=CategorySection.RUNNING_GEAR,
        interval_km=40_000,
        hint="Depinde puternic de stilul de condus și de relief. Se măsoară la fiecare revizie, nu se ghicește.",
    ),
    CategoryDefinition(
        code="placute_spate",
        name="Plăcuțe de frână spate",
        section=CategorySection.RUNNING_GEAR,
        interval_km=60_000,
    ),
    CategoryDefinition(
        code="discuri_fata",
        name="Discuri de frână față",
        section=CategorySection.RUNNING_GEAR,
        interval_km=80_000,
        hint="De obicei la al doilea sau al treilea set de plăcuțe. Semn: vibrație în pedală la frânare de la viteză mare.",
    ),
    CategoryDefinition(
        code="discuri_spate",
        name="Discuri de frână spate",
        section=CategorySection.RUNNING_GEAR,
        interval_km=100_000,
    ),
    CategoryDefinition(
        code="anvelope_vara",
        name="Anvelope de vară",
        section=CategorySection.RUNNING_GEAR,
        interval_km=60_000,
        interval_months=72,
        hint="Cauciucul se întărește cu vârsta. După 6 ani de la data DOT aderența pe umed scade sensibil, chiar dacă profilul pare bun.",
    ),
    CategoryDefinition(
        code="anvelope_iarna",
        name="Anvelope de iarnă",
        section=CategorySection.RUNNING_GEAR,
        interval_km=60_000,
        interval_months=72,
        hint="Sub 4 mm profil, anvelopa de iarnă nu mai face ce trebuie pe zăpadă.",
    ),
    CategoryDefinition(
        code="schimb_sezonier_anvelope",
        name="Schimb sezonier de anvelope",
        section=CategorySection.RUNNING_GEAR,
        interval_months=6,
        hint="Primăvara și toamna. În România, pe drumuri cu zăpadă sau gheață, anvelopele de iarnă sunt obligatorii.",
    ),
    CategoryDefinition(
        code="geometrie",
        name="Geometrie roți",
        section=CategorySection.RUNNING_GEAR,
        interval_km=30_000,
        interval_months=24,
        hint="Obligatoriu după lovituri serioase de bordură sau gropi și după orice înlocuire de piese de direcție. Semn: mașina trage într-o parte sau anvelopele se uzează inegal.",
    ),
    CategoryDefinition(
        code="rotire_anvelope",
        name="Rotire anvelope",
        section=CategorySection.RUNNING_GEAR,
        interval_km=10_000,
        hint="Egalizează uzura între punți și prelungește viața setului.",
    ),
    CategoryDefinition(
        code="amortizoare",
        name="Amortizoare",
        section=CategorySection.RUNNING_GEAR,
        interval_km=100_000,
        hint="Uzura este atât de treptată încât nu se simte. Semne: mașina plutește pe denivelări și distanța de frânare crește.",
    ),
    CategoryDefinition(
        code="bucse_articulatii",
        name="Bucșe, brațe și articulații de direcție",
        section=CategorySection.RUNNING_GEAR,
        interval_km=100_000,
        hint="Se verifică la ITP oricum. Semn: bătăi metalice la trecerea peste denivelări mici.",
    ),
    CategoryDefinition(
        code="rulmenti_roata",
        name="Rulmenți de roată",
        section=CategorySection.RUNNING_GEAR,
        hint="Se schimbă la zgomot, nu la interval. Semn: huruit care crește cu viteza și se schimbă la viraje.",
    ),
    CategoryDefinition(
        code="perne_suspensie",
        name="Perne de suspensie pneumatică",
        section=CategorySection.RUNNING_GEAR,
        interval_km=150_000,
        equipment=(Equipment.AIR_SUSPENSION,),
        hint="Punctul slab clasic al mașinilor cu suspensie pneumatică. Semn: mașina se lasă pe o parte după o noapte de staționare.",
    ),
    CategoryDefinition(
        code="frana_mana",
        name="Frână de mână și cabluri",
        section=CategorySection.RUNNING_GEAR,
        hint="Se reglează la nevoie. Se verifică la ITP.",
    ),
)

ELECTRICAL = (
    CategoryDefinition(
        code="baterie",
        name="Baterie",
        section=CategorySection.ELECTRICAL,
        interval_months=60,
        hint="Ține 4-6 ani și cedează brusc, aproape întotdeauna în prima dimineață cu ger.",
    ),
    CategoryDefinition(
        code="becuri",
        name="Becuri",
        section=CategorySection.ELECTRICAL,
        hint="Se schimbă la ardere. Un far ars înseamnă amendă și ITP respins.",
    ),
    CategoryDefinition(
        code="lamele_stergatoare",
        name="Lamele ștergătoare",
        section=CategorySection.ELECTRICAL,
        interval_months=12,
        hint="Cauciucul se usucă într-un an. Costă puțin și contează enorm la ploaie, noaptea.",
    ),
    CategoryDefinition(
        code="incarcare_clima",
        name="Încărcare instalație de climatizare",
        section=CategorySection.ELECTRICAL,
        interval_months=36,
        equipment=(Equipment.AIR_CONDITIONING,),
        hint="Freonul scade natural, în jur de 10% pe an. Semn: răcește slab în trafic, dar acceptabil la drum.",
    ),
    CategoryDefinition(
        code="dezinfectare_clima",
        name="Dezinfectare instalație de climatizare",
        section=CategorySection.ELECTRICAL,
        interval_months=12,
        equipment=(Equipment.AIR_CONDITIONING,),
        hint="Se face împreună cu filtrul de habitaclu. Rezolvă mirosul de mucegai la pornirea ventilației.",
    ),
    CategoryDefinition(
        code="alternator",
        name="Alternator",
        section=CategorySection.ELECTRICAL,
        fuel_types=COMBUSTION_ENGINES,
        hint="Se schimbă la defect. Semn: martorul de baterie aprins în mers.",
    ),
    CategoryDefinition(
        code="demaror",
        name="Demaror",
        section=CategorySection.ELECTRICAL,
        fuel_types=COMBUSTION_ENGINES,
        hint="Se schimbă la defect. Semn: clic sec la cheie, fără să pornească.",
    ),
    CategoryDefinition(
        code="sonda_lambda",
        name="Sondă lambda",
        section=CategorySection.ELECTRICAL,
        interval_km=150_000,
        fuel_types=PETROL_ENGINES,
        hint="Îmbătrânește lent și crește consumul fără să aprindă neapărat martorul de motor.",
    ),
    CategoryDefinition(
        code="catalizator",
        name="Catalizator",
        section=CategorySection.ELECTRICAL,
        fuel_types=COMBUSTION_ENGINES,
        hint="Se schimbă la defect sau la ITP respins pe emisii.",
    ),
)

OTHER = (
    CategoryDefinition(
        code="spalare_cosmetica",
        name="Spălare și cosmetică",
        section=CategorySection.OTHER,
    ),
    CategoryDefinition(
        code="alta_operatiune",
        name="Altă operațiune",
        section=CategorySection.OTHER,
        hint="Pentru orice nu se regăsește în listă. Scrie în notițe despre ce a fost vorba.",
    ),
)

BUILTIN_CATEGORIES: tuple[CategoryDefinition, ...] = (
    *DOCUMENTS,
    *ENGINE,
    *TRANSMISSION,
    *RUNNING_GEAR,
    *ELECTRICAL,
    *OTHER,
)
