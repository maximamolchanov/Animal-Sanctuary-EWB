import csv
from farm_model_common1 import buildAndRunCase


# run all model cases
allCases = [
    {
        "caseFolder": "case_01_no_drains",
        "caseTitle": "case 1: no tile drains",
        "addTileDrains": False,
        "organicSurface": False,
        "drainSpacingFt": 50,
        "drainDepthM": 1.1,
        "mainDrainDepthM": 1.2,
    },
    {
        "caseFolder": "case_02_50ft_1p1m",
        "caseTitle": "case 2: 50 ft spacing, 1.1 m deep",
        "addTileDrains": True,
        "organicSurface": False,
        "drainSpacingFt": 50,
        "drainDepthM": 1.1,
        "mainDrainDepthM": 1.2,
    },
    {
        "caseFolder": "case_03_50ft_1p1m_organic",
        "caseTitle": "case 3: 50 ft spacing, 1.1 m deep, organic surface",
        "addTileDrains": True,
        "organicSurface": True,
        "drainSpacingFt": 50,
        "drainDepthM": 1.1,
        "mainDrainDepthM": 1.2,
    },
    {
        "caseFolder": "case_04_35ft_1p1m_organic",
        "caseTitle": "case 4: 35 ft spacing, 1.1 m deep, organic surface",
        "addTileDrains": True,
        "organicSurface": True,
        "drainSpacingFt": 35,
        "drainDepthM": 1.1,
        "mainDrainDepthM": 1.2,
    },
    {
        "caseFolder": "case_05_65ft_1p1m_organic",
        "caseTitle": "case 5: 65 ft spacing, 1.1 m deep, organic surface",
        "addTileDrains": True,
        "organicSurface": True,
        "drainSpacingFt": 65,
        "drainDepthM": 1.1,
        "mainDrainDepthM": 1.2,
    },
    {
        "caseFolder": "case_06_50ft_0p9m_organic",
        "caseTitle": "case 6: 50 ft spacing, 0.9 m deep, organic surface",
        "addTileDrains": True,
        "organicSurface": True,
        "drainSpacingFt": 50,
        "drainDepthM": 0.9,
        "mainDrainDepthM": 1.0,
    },
    {
        "caseFolder": "case_07_50ft_1p3m_organic",
        "caseTitle": "case 7: 50 ft spacing, 1.3 m deep, organic surface",
        "addTileDrains": True,
        "organicSurface": True,
        "drainSpacingFt": 50,
        "drainDepthM": 1.3,
        "mainDrainDepthM": 1.4,
    },
    {
        "caseFolder": "case_08_50ft_1p5m_organic",
        "caseTitle": "case 8: 50 ft spacing, 1.5 m deep, organic surface",
        "addTileDrains": True,
        "organicSurface": True,
        "drainSpacingFt": 50,
        "drainDepthM": 1.5,
        "mainDrainDepthM": 1.6,
    },
    {
        "caseFolder": "case_09_35ft_0p9m_organic",
        "caseTitle": "case 9: 35 ft spacing, 0.9 m deep, organic surface",
        "addTileDrains": True,
        "organicSurface": True,
        "drainSpacingFt": 35,
        "drainDepthM": 0.9,
        "mainDrainDepthM": 1.0,
    },
    {
        "caseFolder": "case_10_35ft_1p5m_organic",
        "caseTitle": "case 10: 35 ft spacing, 1.5 m deep, organic surface",
        "addTileDrains": True,
        "organicSurface": True,
        "drainSpacingFt": 35,
        "drainDepthM": 1.5,
        "mainDrainDepthM": 1.6,
    },
    {
        "caseFolder": "case_11_65ft_0p9m_organic",
        "caseTitle": "case 11: 65 ft spacing, 0.9 m deep, organic surface",
        "addTileDrains": True,
        "organicSurface": True,
        "drainSpacingFt": 65,
        "drainDepthM": 0.9,
        "mainDrainDepthM": 1.0,
    },
    {
        "caseFolder": "case_12_65ft_1p5m_organic",
        "caseTitle": "case 12: 65 ft spacing, 1.5 m deep, organic surface",
        "addTileDrains": True,
        "organicSurface": True,
        "drainSpacingFt": 65,
        "drainDepthM": 1.5,
        "mainDrainDepthM": 1.6,
    },
]


# store results here
results = []

for oneCase in allCases:
    result = buildAndRunCase(
        caseFolder=oneCase["caseFolder"],
        caseTitle=oneCase["caseTitle"],
        addTileDrains=oneCase["addTileDrains"],
        organicSurface=oneCase["organicSurface"],
        drainSpacingFt=oneCase["drainSpacingFt"],
        drainDepthM=oneCase["drainDepthM"],
        mainDrainDepthM=oneCase["mainDrainDepthM"],
        showPlot=False,
    )

    results.append(result)


# save summary table
summaryPath = "output/case_summary.csv"

with open(summaryPath, "w", newline="") as file:
    fieldNames = [
        "caseFolder",
        "caseTitle",
        "drainSpacingFt",
        "drainDepthM",
        "organicSurface",
        "avgDepthM",
        "minDepthM",
        "maxDepthM",
        "plotPath",
    ]

    writer = csv.DictWriter(file, fieldnames=fieldNames)
    writer.writeheader()

    for result in results:
        writer.writerow(result)


# print summary
print("")
print("all cases finished")
print(f"summary saved to: {summaryPath}")
print("")

for result in results:
    print(
        result["caseTitle"],
        "| avg depth:",
        round(result["avgDepthM"], 3),
        "m",
        "| min depth:",
        round(result["minDepthM"], 3),
        "m",
    )