from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import flopy


def buildAndRunCase(
    caseFolder,
    caseTitle,
    addTileDrains=True,
    organicSurface=False,
    drainSpacingFt=50,
    drainDepthM=1.1,
    mainDrainDepthM=1.2,
    showPlot=False,
):
    # set output folder
    workspace = Path("output") / caseFolder
    workspace.mkdir(parents=True, exist_ok=True)

    simName = caseFolder
    modelName = "gwfModel"

    # set grid size
    nlay = 1
    nrow = 32
    ncol = 34
    delr = 3.0
    delc = 3.0

    widthM = ncol * delr
    heightM = nrow * delc

    # make 2 m slope from road to creek
    topRoad = 101.0
    topCreek = 99.0

    top = np.zeros((nrow, ncol))

    for row in range(nrow):
        slopeFrac = row / (nrow - 1)
        top[row, :] = topRoad - slopeFrac * (topRoad - topCreek)

    botm = top - 4.0

    # set soil zones
    tukwilaStartRow = 23

    k = np.full((nlay, nrow, ncol), 18.0)
    k33 = np.full((nlay, nrow, ncol), 1.8)

    k[:, tukwilaStartRow:, :] = 0.78
    k33[:, tukwilaStartRow:, :] = 0.078

    # add animal surface effect
    if organicSurface:
        k = np.minimum(k, 0.75)
        k33 = np.minimum(k33, 0.075)

    # set starting water table
    strt = np.zeros((nlay, nrow, ncol))

    strt[:, :tukwilaStartRow, :] = top[:tukwilaStartRow, :] - 2.0
    strt[:, tukwilaStartRow:, :] = top[tukwilaStartRow:, :] - 0.1

    if organicSurface:
        wetStart = top - 0.5
        strt[0, :, :] = np.maximum(strt[0, :, :], wetStart)

    strt = np.maximum(strt, botm + 0.2)

    # set recharge
    recharge = np.full((nrow, ncol), 0.001)
    recharge[tukwilaStartRow:, :] = 0.002

    if organicSurface:
        recharge = np.maximum(recharge, 0.003)

    # make simulation
    sim = flopy.mf6.MFSimulation(
        sim_name=simName,
        exe_name="mf6",
        sim_ws=str(workspace),
    )

    flopy.mf6.ModflowTdis(
        sim,
        time_units="DAYS",
        nper=1,
        perioddata=[(365.0, 365, 1.0)],
    )

    flopy.mf6.ModflowIms(
        sim,
        complexity="SIMPLE",
    )

    gwf = flopy.mf6.ModflowGwf(
        sim,
        modelname=modelName,
        save_flows=True,
    )

    flopy.mf6.ModflowGwfdis(
        gwf,
        nlay=nlay,
        nrow=nrow,
        ncol=ncol,
        delr=delr,
        delc=delc,
        top=top,
        botm=botm,
    )

    flopy.mf6.ModflowGwfic(
        gwf,
        strt=strt,
    )

    flopy.mf6.ModflowGwfnpf(
        gwf,
        icelltype=1,
        k=k,
        k33=k33,
        save_specific_discharge=True,
    )

    flopy.mf6.ModflowGwfsto(
        gwf,
        iconvert=1,
        sy=0.15,
        ss=1e-5,
        transient={0: True},
    )

    flopy.mf6.ModflowGwfrcha(
        gwf,
        recharge=recharge,
    )

    # add creek at bottom
    riverData = []
    creekRow = nrow - 1

    for col in range(ncol):
        stage = top[creekRow, col] - 0.25
        riverBottom = top[creekRow, col] - 0.75
        conductance = 50.0
        riverData.append(((0, creekRow, col), stage, conductance, riverBottom))

    flopy.mf6.ModflowGwfriv(
        gwf,
        stress_period_data=riverData,
    )

    # add tile drains
    drainRows = []

    if addTileDrains:
        spacingM = drainSpacingFt * 0.3048
        rowGap = max(2, round(spacingM / delc))

        drainRows = list(range(rowGap, nrow - 1, rowGap))

        drainDict = {}

        def addDrain(cellId, elev, cond):
            if cellId in drainDict:
                oldElev, oldCond = drainDict[cellId]
                drainDict[cellId] = (min(oldElev, elev), oldCond + cond)
            else:
                drainDict[cellId] = (elev, cond)

        # add horizontal drains
        for row in drainRows:
            for col in range(2, ncol - 2):
                drainElev = top[row, col] - drainDepthM
                addDrain((0, row, col), drainElev, 25.0)

        # add main drain
        mainCol = ncol - 5

        for row in range(3, nrow):
            drainElev = top[row, mainCol] - mainDrainDepthM
            addDrain((0, row, mainCol), drainElev, 70.0)

        drains = []

        for cellId, drainInfo in drainDict.items():
            drainElev, drainCond = drainInfo
            drains.append((cellId, drainElev, drainCond))

        flopy.mf6.ModflowGwfdrn(
            gwf,
            stress_period_data={0: drains},
            save_flows=True,
        )

    # set output
    flopy.mf6.ModflowGwfoc(
        gwf,
        head_filerecord=f"{modelName}.hds",
        budget_filerecord=f"{modelName}.cbc",
        saverecord=[("HEAD", "LAST"), ("BUDGET", "LAST")],
        printrecord=[("BUDGET", "LAST")],
    )

    # run model
    sim.write_simulation()
    success, message = sim.run_simulation()

    if not success:
        raise RuntimeError(f"{caseTitle} failed")

    print(f"{caseTitle} finished")

    # read heads
    headFile = workspace / f"{modelName}.hds"
    heads = flopy.utils.HeadFile(str(headFile))
    head = heads.get_data()[0]

    depthToWater = top - head

    avgDepth = float(np.mean(depthToWater))
    minDepth = float(np.min(depthToWater))
    maxDepth = float(np.max(depthToWater))

    # plot result
    fig, ax = plt.subplots(figsize=(10, 7))

    image = ax.imshow(
        depthToWater,
        origin="upper",
        extent=[0, widthM, heightM, 0],
        aspect="equal",
    )

    cbar = plt.colorbar(image, ax=ax)
    cbar.set_label("depth to water table below ground (m)")

    ax.set_title(caseTitle)
    ax.set_xlabel("distance left-to-right across property (m)")
    ax.set_ylabel("distance from road/top toward creek/bottom (m)")

    ax.text(
        2,
        4,
        "road / upper property",
        fontsize=9,
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
    )

    ax.axhline(
        y=heightM - 0.5,
        color="blue",
        linewidth=2,
        label="creek boundary",
    )

    ax.text(
        2,
        heightM - 3,
        "creek / lower property",
        fontsize=9,
        color="blue",
        bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
    )

    tukwilaY = tukwilaStartRow * delc

    ax.axhline(
        y=tukwilaY,
        color="cyan",
        linestyle="--",
        linewidth=1.5,
        label="approx tukwila muck start",
    )

    if organicSurface:
        ax.text(
            widthM * 0.38,
            8,
            "animal/organic surface effect",
            fontsize=9,
            bbox=dict(facecolor="white", alpha=0.75, edgecolor="none"),
        )

    if addTileDrains:
        for row in drainRows:
            y = row * delc
            ax.axhline(y=y, color="white", linewidth=1.2, alpha=0.9)

        mainCol = ncol - 5
        x = mainCol * delr

        ax.axvline(
            x=x,
            color="red",
            linewidth=2,
            label="main drain to creek",
        )

        ax.text(
            x + 1,
            heightM * 0.55,
            "main drain",
            fontsize=9,
            color="red",
            bbox=dict(facecolor="white", alpha=0.7, edgecolor="none"),
        )

    ax.legend(loc="upper right", fontsize=8)
    plt.tight_layout()

    plotPath = workspace / f"{caseFolder}_plot.png"
    plt.savefig(plotPath, dpi=200)

    if showPlot:
        plt.show()
    else:
        plt.close()

    print(f"saved plot to: {plotPath}")

    return {
        "caseFolder": caseFolder,
        "caseTitle": caseTitle,
        "drainSpacingFt": drainSpacingFt,
        "drainDepthM": drainDepthM,
        "organicSurface": organicSurface,
        "avgDepthM": avgDepth,
        "minDepthM": minDepth,
        "maxDepthM": maxDepth,
        "plotPath": str(plotPath),
    }