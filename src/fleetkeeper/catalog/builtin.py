"""The built-in service catalogue, in Romanian, as the interface presents it.

Every interval carries the source it came from, because a published service figure and a
number a workshop finds reasonable are different claims and should not look alike. Where
no defensible figure exists the interval is left out and the explanation says what to look
for instead: a wear part gets an inspection cadence, and a symptom-driven job gets none.

None of this is authoritative for a specific engine code. The explanations name the range
that is commonly quoted and point at the car's own service plan, and every interval is
editable per vehicle once a car is added.
"""

from dataclasses import dataclass

from fleetkeeper.models.enums import (
    CategoryKind,
    CategorySection,
    Drivetrain,
    Equipment,
    FuelType,
    GearboxType,
    IntervalSource,
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
    source: IntervalSource | None = None
    fuel_types: tuple[FuelType, ...] = ()
    gearbox_types: tuple[GearboxType, ...] = ()
    drivetrains: tuple[Drivetrain, ...] = ()
    equipment: tuple[Equipment, ...] = ()
    hint: str | None = None

    def __post_init__(self) -> None:
        has_interval = self.interval_km is not None or self.interval_months is not None
        if has_interval != (self.source is not None):
            raise ValueError(f"{self.code}: an interval and its source must be given together")


DOCUMENTS = (
    CategoryDefinition(
        code="rca",
        name="Asigurare RCA",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="Obligatorie prin lege. Se poate încheia pe 1, 6 sau 12 luni, iar scadența este data trecută pe poliță — o folosim pe aceea, nu o calculăm noi.",
    ),
    CategoryDefinition(
        code="itp",
        name="Inspecție tehnică periodică (ITP)",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="Obligatorie prin lege. La autoturisme cadența este de regulă la 2 ani și devine anuală pentru mașinile vechi, dar regulile s-au schimbat în timp. Scadența pe care o urmărim este data următoarei inspecții trecută pe fișa ITP.",
    ),
    CategoryDefinition(
        code="rovinieta",
        name="Rovinietă",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="Obligatorie pe drumurile naționale și autostrăzi. Se cumpără pe zile, luni sau un an; scadența este sfârșitul perioadei plătite.",
    ),
    CategoryDefinition(
        code="casco",
        name="Asigurare CASCO",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="Opțională. Perioada și acoperirea sunt cele din poliță.",
    ),
    CategoryDefinition(
        code="vigneta_externa",
        name="Vinietă pentru străinătate",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="Ungaria, Austria, Slovacia și altele au fiecare sistemul propriu, cu prețuri și perioade diferite. Se cumpără înainte de a intra pe drumul cu taxă.",
    ),
    CategoryDefinition(
        code="verificare_gpl",
        name="Verificare instalație GPL",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        equipment=(Equipment.LPG_SYSTEM,),
        hint="Verificare periodică obligatorie pentru instalațiile de gaz, fără care nu se obține ITP-ul. Cadența și scadența sunt cele din documentul eliberat la verificare.",
    ),
    CategoryDefinition(
        code="extinctor",
        name="Extinctor",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="Data de expirare este inscripționată pe corpul extinctorului. Se verifică la ITP.",
    ),
    CategoryDefinition(
        code="kit_prim_ajutor",
        name="Kit de prim ajutor",
        section=CategorySection.DOCUMENTS,
        kind=CategoryKind.DOCUMENT,
        hint="Expiră, la fel ca medicamentele din el. Data este pe ambalaj.",
    ),
)

ENGINE = (
    CategoryDefinition(
        code="ulei_motor",
        name="Ulei de motor și filtru de ulei",
        section=CategorySection.ENGINE,
        interval_km=15_000,
        interval_months=12,
        source=IntervalSource.MANUFACTURER,
        fuel_types=COMBUSTION_ENGINES,
        hint="Multe mașini au două scheme de service: una fixă, la 15.000 km sau 12 luni, și una extinsă, care merge mai departe pe baza senzorilor. Valoarea implicită este schema fixă, cea mai conservatoare. Pentru diesel cu filtru de particule folosit pe drumuri scurte, atelierele recomandă adesea 10.000 km. Verifică ce schemă are mașina ta în manual.",
    ),
    CategoryDefinition(
        code="filtru_aer",
        name="Filtru de aer",
        section=CategorySection.ENGINE,
        interval_km=30_000,
        interval_months=24,
        source=IntervalSource.PRACTICE,
        fuel_types=COMBUSTION_ENGINES,
        hint="Se citează între 30.000 și 60.000 km, în funcție de motor și de cât praf înghite mașina. Valoarea implicită este capătul conservator; verifică planul de service.",
    ),
    CategoryDefinition(
        code="filtru_habitaclu",
        name="Filtru de habitaclu (polen)",
        section=CategorySection.ENGINE,
        interval_km=15_000,
        interval_months=12,
        source=IntervalSource.MANUFACTURER,
        hint="De regulă la fiecare revizie. Când se înfundă, geamurile se dezaburesc greu și apare miros de umezeală la pornirea ventilației.",
    ),
    CategoryDefinition(
        code="filtru_combustibil",
        name="Filtru de combustibil",
        section=CategorySection.ENGINE,
        interval_km=60_000,
        interval_months=48,
        source=IntervalSource.PRACTICE,
        fuel_types=DIESEL_ENGINES,
        hint="La diesel se citează în jur de 60.000 km, dar diferă pe coduri de motor — verifică manualul. La benzină este de obicei montat în rezervor și nu se schimbă periodic.",
    ),
    CategoryDefinition(
        code="bujii",
        name="Bujii",
        section=CategorySection.ENGINE,
        interval_km=40_000,
        source=IntervalSource.PRACTICE,
        fuel_types=PETROL_ENGINES,
        hint="Depinde puternic de tipul bujiei și de motor: la motoarele supraalimentate se citează 30.000-40.000 km, la cele aspirate se poate merge spre 60.000-90.000 km. Valoarea implicită este cea conservatoare. Verifică specificația din manual și corectează aici.",
    ),
    CategoryDefinition(
        code="bujii_incandescente",
        name="Bujii incandescente",
        section=CategorySection.ENGINE,
        fuel_types=DIESEL_ENGINES,
        hint="Nu au interval de schimb: se înlocuiesc la defect. Semnul clar este pornirea greoaie pe vreme rece, uneori însoțită de martor de motor.",
    ),
    CategoryDefinition(
        code="lichid_racire",
        name="Lichid de răcire (antigel)",
        section=CategorySection.ENGINE,
        interval_months=60,
        source=IntervalSource.PRACTICE,
        hint="Multe mașini moderne îl declară „pe viață”. Atelierele îl schimbă totuși la 4-6 ani, fiindcă își pierde proprietățile anticorozive chiar dacă arată curat. Valoarea implicită urmează practica de atelier, nu manualul. Tipurile de antigel nu se amestecă — verifică specificația (de exemplu G12 sau G13).",
    ),
    CategoryDefinition(
        code="lichid_frana",
        name="Lichid de frână",
        section=CategorySection.ENGINE,
        interval_months=24,
        source=IntervalSource.MANUFACTURER,
        hint="Se schimbă după timp, nu după kilometri: absoarbe apă din aer chiar și cu mașina în garaj, iar apa fierbe la frânări repetate și pedala se duce în podea. La multe mașini prima schimbare este la 3 ani și apoi la fiecare 2 — verifică planul de service.",
    ),
    CategoryDefinition(
        code="curea_distributie",
        name="Curea de distribuție, pompă de apă și role",
        section=CategorySection.ENGINE,
        interval_km=120_000,
        interval_months=72,
        source=IntervalSource.PRACTICE,
        equipment=(Equipment.TIMING_BELT,),
        hint="Cea mai scumpă lucrare amânată: dacă cureaua cedează, motorul se distruge. Atenție, intervalul diferă mult pe coduri de motor și a fost revizuit de producători de mai multe ori — se citează între 90.000 și 180.000 km. Valoarea implicită este conservatoare, dar caută intervalul exact pentru codul motorului tău și corectează-l aici. Se schimbă împreună cu pompa de apă și rolele, fiindcă manopera este aceeași.",
    ),
    CategoryDefinition(
        code="curea_accesorii",
        name="Curea de accesorii",
        section=CategorySection.ENGINE,
        kind=CategoryKind.INSPECTION,
        interval_km=30_000,
        source=IntervalSource.PRACTICE,
        fuel_types=COMBUSTION_ENGINES,
        hint="Se verifică vizual la revizii — fisuri, luciu, franjuri pe margine — și se schimbă la semne de uzură, nu la interval fix. Semn sonor: fluierat la pornirea la rece.",
    ),
    CategoryDefinition(
        code="adblue",
        name="Verificare nivel AdBlue",
        section=CategorySection.ENGINE,
        kind=CategoryKind.INSPECTION,
        interval_km=15_000,
        source=IntervalSource.ESTIMATE,
        equipment=(Equipment.ADBLUE,),
        hint="Se completează în funcție de consum, nu la interval fix — orientativ în jur de 1-2 litri la 1.000 km, dar depinde de motor și de stilul de condus. Mașina avertizează singură când scade. Dacă rezervorul se golește complet, motorul nu mai pornește după ce îl oprești.",
    ),
    CategoryDefinition(
        code="curatare_dpf",
        name="Curățare filtru de particule (DPF)",
        section=CategorySection.ENGINE,
        equipment=(Equipment.PARTICULATE_FILTER,),
        hint="Nu are interval de service: se colmatează în funcție de cum este folosită mașina. La drumuri exclusiv scurte nu ajunge la temperatura de regenerare. Semne: consum crescut, regenerări tot mai frecvente, martor aprins.",
    ),
    CategoryDefinition(
        code="curatare_egr",
        name="Curățare EGR și clapetă de admisie",
        section=CategorySection.ENGINE,
        fuel_types=DIESEL_ENGINES,
        hint="Nu are interval de service. Se cocsează cu funingine, mai ales la mers scurt în oraș. Semne: pierdere de putere, mers neregulat la ralanti, martor de motor.",
    ),
    CategoryDefinition(
        code="injectoare",
        name="Verificare injectoare",
        section=CategorySection.ENGINE,
        fuel_types=COMBUSTION_ENGINES,
        hint="Se verifică la simptome, nu la interval. Semne: mers neregulat, fum, consum crescut, pornire greoaie.",
    ),
    CategoryDefinition(
        code="revizie_generala",
        name="Revizie generală la service",
        section=CategorySection.ENGINE,
        interval_km=15_000,
        interval_months=12,
        source=IntervalSource.MANUFACTURER,
        hint="Verificarea periodică completă, dincolo de schimbul de ulei: nivele, uzuri, jocuri, erori din calculator. Cadența urmează schema de service a mașinii.",
    ),
)

TRANSMISSION = (
    CategoryDefinition(
        code="ulei_cutie_manuala",
        name="Ulei cutie manuală",
        section=CategorySection.TRANSMISSION,
        interval_km=120_000,
        source=IntervalSource.PRACTICE,
        gearbox_types=(GearboxType.MANUAL,),
        hint="Producătorii îl declară de obicei „pe viață”. Atelierele îl schimbă în jur de 100.000-150.000 km, fiindcă uleiul obosit se aude ca zgomot în trepte și se simte la schimbări la rece. Valoarea implicită urmează practica, nu manualul.",
    ),
    CategoryDefinition(
        code="ulei_cutie_automata",
        name="Ulei și filtru cutie automată",
        section=CategorySection.TRANSMISSION,
        interval_km=80_000,
        interval_months=96,
        source=IntervalSource.PRACTICE,
        gearbox_types=(GearboxType.TORQUE_CONVERTER,),
        hint="„Pe viață” este formulare comercială, nu inginerie. Producătorii de cutii recomandă schimbul în jur de 80.000-120.000 km. Semne de ulei obosit: șocuri sau ezitări la trecerea treptelor. Verifică recomandarea producătorului cutiei din mașina ta, nu doar a mașinii.",
    ),
    CategoryDefinition(
        code="ulei_dsg_umed",
        name="Ulei și filtru cutie cu ambreiaj dublu umed",
        section=CategorySection.TRANSMISSION,
        interval_km=60_000,
        interval_months=48,
        source=IntervalSource.MANUFACTURER,
        gearbox_types=(GearboxType.DUAL_CLUTCH_WET,),
        hint="La cutiile cu ambreiaj umed uleiul răcește și ambreiajele, deci contează. Se schimbă împreună cu filtrul.",
    ),
    CategoryDefinition(
        code="fluid_mecatronica_dsg",
        name="Fluid mecatronică (ambreiaj dublu uscat)",
        section=CategorySection.TRANSMISSION,
        interval_km=60_000,
        interval_months=48,
        source=IntervalSource.PRACTICE,
        gearbox_types=(GearboxType.DUAL_CLUTCH_DRY,),
        hint="La cutiile cu ambreiaj uscat, uleiul de cutie este pe viață, dar fluidul hidraulic al mecatronicii nu. Se citează în jur de 60.000 km. Se ratează foarte des, fiindcă lumea aude „pe viață” și se oprește acolo, iar mecatronica defectă este o reparație scumpă. Confirmă intervalul în planul de service al mașinii.",
    ),
    CategoryDefinition(
        code="ulei_cvt",
        name="Ulei cutie CVT",
        section=CategorySection.TRANSMISSION,
        interval_km=60_000,
        source=IntervalSource.PRACTICE,
        gearbox_types=(GearboxType.CVT,),
        hint="Se citează în jur de 60.000 km, dar diferă mult între producători, iar cutiile CVT sunt sensibile la uleiul greșit. Verifică manualul înainte.",
    ),
    CategoryDefinition(
        code="ulei_diferential",
        name="Ulei diferențial",
        section=CategorySection.TRANSMISSION,
        interval_km=120_000,
        source=IntervalSource.PRACTICE,
        drivetrains=(Drivetrain.REAR, Drivetrain.ALL),
        hint="La tracțiune față diferențialul este integrat în cutie și nu are ulei separat. La tracțiune spate sau integrală, intervalul diferă pe modele — verifică manualul.",
    ),
    CategoryDefinition(
        code="ulei_haldex",
        name="Ulei și filtru cuplaj punte spate",
        section=CategorySection.TRANSMISSION,
        interval_km=60_000,
        source=IntervalSource.PRACTICE,
        drivetrains=(Drivetrain.ALL,),
        hint="Multe sisteme de tracțiune integrală au pe puntea spate un cuplaj cu ulei propriu, care se citează la schimb în jur de 60.000 km, cu filtrul la fiecare a doua schimbare. Se uită aproape întotdeauna. Verifică întâi dacă mașina ta are acest tip de cuplaj — nu toate sistemele integrale îl folosesc.",
    ),
    CategoryDefinition(
        code="kit_ambreiaj",
        name="Kit ambreiaj și volantă",
        section=CategorySection.TRANSMISSION,
        gearbox_types=(GearboxType.MANUAL, *DUAL_CLUTCH),
        hint="Nu are interval: se schimbă la uzură. Semne: patinare la accelerare în treaptă mare, pedală moale, miros de ars la plecări în rampă.",
    ),
)

RUNNING_GEAR = (
    CategoryDefinition(
        code="placute_fata",
        name="Plăcuțe de frână față",
        section=CategorySection.RUNNING_GEAR,
        kind=CategoryKind.INSPECTION,
        interval_km=15_000,
        interval_months=12,
        source=IntervalSource.MANUFACTURER,
        hint="Nu au interval de înlocuire, se măsoară. Verificarea sistemului de frânare face parte din revizia periodică, iar intervalul de aici este cadența de verificare, nu de schimb. Durata reală variază enorm cu stilul de condus și relieful, de la 20.000 la peste 80.000 km.",
    ),
    CategoryDefinition(
        code="placute_spate",
        name="Plăcuțe de frână spate",
        section=CategorySection.RUNNING_GEAR,
        kind=CategoryKind.INSPECTION,
        interval_km=15_000,
        interval_months=12,
        source=IntervalSource.MANUFACTURER,
        hint="Se măsoară, la fel ca cele din față, și de obicei țin mai mult.",
    ),
    CategoryDefinition(
        code="discuri_fata",
        name="Discuri de frână față",
        section=CategorySection.RUNNING_GEAR,
        kind=CategoryKind.INSPECTION,
        interval_km=15_000,
        interval_months=12,
        source=IntervalSource.MANUFACTURER,
        hint="Se măsoară grosimea, iar limita minimă este ștanțată pe disc. De obicei se ajunge la schimb la al doilea sau al treilea set de plăcuțe. Semn: vibrație în pedală la frânare de la viteză mare.",
    ),
    CategoryDefinition(
        code="discuri_spate",
        name="Discuri de frână spate",
        section=CategorySection.RUNNING_GEAR,
        kind=CategoryKind.INSPECTION,
        interval_km=15_000,
        interval_months=12,
        source=IntervalSource.MANUFACTURER,
        hint="Se măsoară grosimea, cu limita minimă ștanțată pe disc.",
    ),
    CategoryDefinition(
        code="anvelope_vara",
        name="Anvelope de vară",
        section=CategorySection.RUNNING_GEAR,
        kind=CategoryKind.INSPECTION,
        interval_months=12,
        source=IntervalSource.PRACTICE,
        hint="Se verifică profilul și vârsta, nu se schimbă la kilometraj. Minimul legal în Uniunea Europeană este 1,6 mm, iar sub 3 mm aderența pe umed scade sensibil. Cauciucul se întărește cu anii: după 6 ani de la data DOT ștanțată pe flanc merită verificat cu atenție, indiferent cât profil a mai rămas.",
    ),
    CategoryDefinition(
        code="anvelope_iarna",
        name="Anvelope de iarnă",
        section=CategorySection.RUNNING_GEAR,
        kind=CategoryKind.INSPECTION,
        interval_months=12,
        source=IntervalSource.PRACTICE,
        hint="Minimul legal este același 1,6 mm, dar sub 4 mm o anvelopă de iarnă nu mai face ce trebuie pe zăpadă. Verifică și data DOT.",
    ),
    CategoryDefinition(
        code="schimb_sezonier_anvelope",
        name="Schimb sezonier de anvelope",
        section=CategorySection.RUNNING_GEAR,
        interval_months=6,
        source=IntervalSource.PRACTICE,
        hint="Primăvara și toamna, orientativ în jurul pragului de 7 grade Celsius, sub care cauciucul de vară se întărește. În România, pe drumuri acoperite cu zăpadă sau gheață, anvelopele de iarnă sunt obligatorii prin lege.",
    ),
    CategoryDefinition(
        code="geometrie",
        name="Geometrie roți",
        section=CategorySection.RUNNING_GEAR,
        kind=CategoryKind.INSPECTION,
        interval_km=30_000,
        source=IntervalSource.PRACTICE,
        hint="Nu este o operațiune programată. Se verifică după lovituri serioase de bordură sau gropi și obligatoriu după înlocuirea pieselor de direcție. Semne: mașina trage într-o parte, volanul nu stă drept, anvelopele se uzează inegal pe o margine.",
    ),
    CategoryDefinition(
        code="rotire_anvelope",
        name="Rotire anvelope",
        section=CategorySection.RUNNING_GEAR,
        interval_km=10_000,
        source=IntervalSource.PRACTICE,
        hint="Convenție de atelier, ca uzura să se egalizeze între punți. Nu toți producătorii o recomandă și la unele mașini nu se aplică — verifică manualul.",
    ),
    CategoryDefinition(
        code="amortizoare",
        name="Amortizoare",
        section=CategorySection.RUNNING_GEAR,
        kind=CategoryKind.INSPECTION,
        interval_months=24,
        source=IntervalSource.PRACTICE,
        hint="Nu au interval de înlocuire. Se verifică la ITP și la revizii, fiindcă uzura este atât de treptată încât nu se simte. Semne: mașina plutește pe denivelări, se leagănă după o groapă, distanța de frânare crește.",
    ),
    CategoryDefinition(
        code="bucse_articulatii",
        name="Bucșe, brațe și articulații de direcție",
        section=CategorySection.RUNNING_GEAR,
        kind=CategoryKind.INSPECTION,
        interval_months=24,
        source=IntervalSource.PRACTICE,
        hint="Se verifică la ITP și se schimbă la joc. Semn: bătăi metalice la trecerea peste denivelări mici.",
    ),
    CategoryDefinition(
        code="rulmenti_roata",
        name="Rulmenți de roată",
        section=CategorySection.RUNNING_GEAR,
        kind=CategoryKind.INSPECTION,
        interval_months=24,
        source=IntervalSource.PRACTICE,
        hint="Se verifică la ITP și se schimbă la zgomot, nu la interval. Semn: huruit care crește cu viteza și se schimbă la viraje.",
    ),
    CategoryDefinition(
        code="perne_suspensie",
        name="Perne de suspensie pneumatică",
        section=CategorySection.RUNNING_GEAR,
        kind=CategoryKind.INSPECTION,
        interval_months=24,
        source=IntervalSource.ESTIMATE,
        equipment=(Equipment.AIR_SUSPENSION,),
        hint="Nu au interval de înlocuire, iar durata variază foarte mult. Sunt punctul slab clasic al suspensiei pneumatice. Semne: mașina se lasă pe o parte sau în față după o noapte de staționare, compresorul pornește des sau se aude mai mult decât înainte.",
    ),
    CategoryDefinition(
        code="frana_mana",
        name="Frână de mână și cabluri",
        section=CategorySection.RUNNING_GEAR,
        kind=CategoryKind.INSPECTION,
        interval_months=24,
        source=IntervalSource.PRACTICE,
        hint="Se verifică la ITP și se reglează la nevoie.",
    ),
)

ELECTRICAL = (
    CategoryDefinition(
        code="baterie",
        name="Baterie",
        section=CategorySection.ELECTRICAL,
        kind=CategoryKind.INSPECTION,
        interval_months=12,
        source=IntervalSource.PRACTICE,
        hint="Nu are interval de înlocuire. Se testează, ideal toamna, înainte de primul ger. Orientativ ține 4-6 ani, dar cedează brusc și aproape întotdeauna în prima dimineață rece.",
    ),
    CategoryDefinition(
        code="becuri",
        name="Becuri",
        section=CategorySection.ELECTRICAL,
        kind=CategoryKind.INSPECTION,
        interval_months=6,
        source=IntervalSource.PRACTICE,
        hint="Se verifică printr-un ocol în jurul mașinii, cu luminile aprinse și cu cineva care apasă frâna și semnalizarea. Un bec ars înseamnă amendă și ITP respins.",
    ),
    CategoryDefinition(
        code="lamele_stergatoare",
        name="Lamele ștergătoare",
        section=CategorySection.ELECTRICAL,
        kind=CategoryKind.INSPECTION,
        interval_months=12,
        source=IntervalSource.PRACTICE,
        hint="Cauciucul se usucă într-un an. Semn: lasă dungi sau sare peste parbriz. Costă puțin și contează enorm la ploaie, noaptea.",
    ),
    CategoryDefinition(
        code="incarcare_clima",
        name="Încărcare instalație de climatizare",
        section=CategorySection.ELECTRICAL,
        interval_months=36,
        source=IntervalSource.PRACTICE,
        equipment=(Equipment.AIR_CONDITIONING,),
        hint="Convenție de atelier: agentul frigorific scade natural, orientativ în jur de 10% pe an, deci se completează la câțiva ani. Semn: răcește slab în trafic, dar acceptabil la drum. Dacă scade rapid, nu se completează — se caută scurgerea.",
    ),
    CategoryDefinition(
        code="dezinfectare_clima",
        name="Dezinfectare instalație de climatizare",
        section=CategorySection.ELECTRICAL,
        interval_months=12,
        source=IntervalSource.PRACTICE,
        equipment=(Equipment.AIR_CONDITIONING,),
        hint="Se face împreună cu filtrul de habitaclu. Rezolvă mirosul de mucegai la pornirea ventilației.",
    ),
    CategoryDefinition(
        code="alternator",
        name="Alternator",
        section=CategorySection.ELECTRICAL,
        fuel_types=COMBUSTION_ENGINES,
        hint="Nu are interval: se schimbă la defect. Semne: martorul de baterie aprins în mers, faruri care pălesc la ralanti, baterie care se descarcă fără motiv.",
    ),
    CategoryDefinition(
        code="demaror",
        name="Demaror",
        section=CategorySection.ELECTRICAL,
        fuel_types=COMBUSTION_ENGINES,
        hint="Nu are interval: se schimbă la defect. Semn: clic sec la cheie, fără să pornească, deși bateria este bună.",
    ),
    CategoryDefinition(
        code="sonda_lambda",
        name="Sondă lambda",
        section=CategorySection.ELECTRICAL,
        fuel_types=PETROL_ENGINES,
        hint="Nu are interval de service. Îmbătrânește lent și crește consumul fără să aprindă neapărat martorul de motor. Se verifică la diagnoză, dacă apare consum nejustificat.",
    ),
    CategoryDefinition(
        code="catalizator",
        name="Catalizator",
        section=CategorySection.ELECTRICAL,
        fuel_types=COMBUSTION_ENGINES,
        hint="Nu are interval: se schimbă la defect sau la ITP respins pe emisii.",
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
        hint="Pentru orice nu se regăsește în listă. Scrie în notițe despre ce a fost vorba, iar dacă se repetă la un interval, poți adăuga o operațiune proprie cu intervalul tău.",
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
