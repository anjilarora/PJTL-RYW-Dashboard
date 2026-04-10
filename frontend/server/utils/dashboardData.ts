export const dashboardData = {
  asOf: "2026-04-15",
  sourceNote:
    "Historical operating metrics come from the frozen daily-metrics base, intake programs and program economics come from the example prospective workbook, and margin/readiness outputs remain assumption-backed where the source formula is still unresolved.",
  shell: {
    productName: "Ride YourWay",
    productTagline: "Market viability dashboard",
    breadcrumb: ["Ride YourWay", "Dashboard"],
    sidebar: [
      { label: "Dashboard", badge: "Live", active: true },
      { label: "Partner Intake", badge: "8 rows", active: false },
      { label: "Master Inputs", badge: "Tiered", active: false },
      { label: "Kent-Leg Logic", badge: "Dual", active: false },
      { label: "Market Rollup", badge: "MVP", active: false },
      { label: "Assumptions", badge: "4 open", active: false }
    ]
  },
  market: {
    name: "Example Medical Center",
    corridor: "Grand Rapids North Corridor",
    cityState: "Grand Rapids, MI",
    status: "No-Go",
    confidence: "Tier 2 Assumption-Backed",
    summary:
      "The example market has enough density to operate, but it still misses the current launch standard on revenue density, projected margin, and concentration under the frozen MVP assumptions."
  },
  readiness: {
    score: 66.7,
    passingCount: 5,
    provisionalCount: 2,
    failingCount: 2,
    totalConditions: 9,
    projectedMarginPct: -3.19,
    targetMarginPct: 25,
    projectedWeeklyRevenue: 8772.0,
    projectedRevenuePerKentLeg: 61.96,
    targetRevenuePerKentLeg: 70.0,
    projectedRoadHoursPerVehicleDay: 9.05,
    projectedHigherAcuitySharePct: 9.89,
    decisionNote:
      "Five conditions pass cleanly, two remain provisional because the formula is still unresolved, and two fail on the current intake mix."
  },
  historical: {
    totalRevenue: 433601.32,
    totalKentLegs: 10819.59,
    revenuePerKentLeg: 40.08,
    completedTrips: 4248,
    billedNoShows: 391,
    nonBillableNoShows: 657,
    totalRoadHours: 6687.97,
    vehicleDays: 772,
    roadHoursPerVehicleDay: 8.66,
    vehicleDaysOverNineHoursPct: 39.5,
    topPayerRevenueShare: 14.01,
    modeMix: [
      {
        label: "Wheelchair",
        trips: 4196,
        revenue: 206176.85,
        kentLegs: 4962.56,
        revenuePerKentLeg: 41.55
      },
      {
        label: "Ambulatory",
        trips: 3745,
        revenue: 168744.65,
        kentLegs: 5647.53,
        revenuePerKentLeg: 29.88
      },
      {
        label: "Stretcher",
        trips: 146,
        revenue: 58679.82,
        kentLegs: 209.5,
        revenuePerKentLeg: 280.1
      }
    ],
    weeklyMargins: [
      { week: "Week 1", revenue: 109173.6, cost: 129801.06, marginPct: -18.89 },
      { week: "Week 2", revenue: 176938.64, cost: 154515.28, marginPct: 12.67 },
      { week: "Week 3", revenue: 191137.44, cost: 154816.44, marginPct: 19.0 },
      { week: "Week 4", revenue: 165758.72, cost: 146674.64, marginPct: 11.51 },
      { week: "Week 5", revenue: 189549.5, cost: 149809.38, marginPct: 20.97 }
    ],
    topPayers: [
      {
        name: "Battle Creek VA",
        weeklyTrips: 460.2,
        weeklyCompletedTrips: 128.2,
        weeklyRevenue: 12152.1,
        weeklyKentLegs: 685.4,
        avgRevenuePerKentLeg: 17.73,
        completionPct: 27.9
      },
      {
        name: "SafeRide Health - Priority Medicaid",
        weeklyTrips: 250.2,
        weeklyCompletedTrips: 168.0,
        weeklyRevenue: 11021.82,
        weeklyKentLegs: 367.5,
        avgRevenuePerKentLeg: 30.0,
        completionPct: 67.1
      },
      {
        name: "MTM",
        weeklyTrips: 156.8,
        weeklyCompletedTrips: 85.6,
        weeklyRevenue: 8614.64,
        weeklyKentLegs: 237.0,
        avgRevenuePerKentLeg: 36.35,
        completionPct: 54.6
      },
      {
        name: "Valley View Care Center",
        weeklyTrips: 45.6,
        weeklyCompletedTrips: 32.8,
        weeklyRevenue: 7006.0,
        weeklyKentLegs: 45.6,
        avgRevenuePerKentLeg: 153.64,
        completionPct: 71.9
      },
      {
        name: "PP",
        weeklyTrips: 96.8,
        weeklyCompletedTrips: 55.8,
        weeklyRevenue: 5216.6,
        weeklyKentLegs: 107.8,
        avgRevenuePerKentLeg: 48.41,
        completionPct: 57.6
      }
    ],
    projectedCostBreakdown: [
      { label: "Driver wage", amount: 3454.59, sharePct: 38.17 },
      { label: "Fixed overhead", amount: 2615.8, sharePct: 28.9 },
      { label: "Fixed operating", amount: 2297.38, sharePct: 25.38 },
      { label: "Gas", amount: 697.81, sharePct: 7.71 }
    ]
  },
  prospective: {
    weeklyRevenue: 8772.0,
    completedTripsPerWeek: 91,
    billableNoShowsPerWeek: 9,
    nonBillableNoShowsPerWeek: 5,
    qualitySharePct: 84.62,
    higherAcuitySharePct: 9.89,
    projectedKentLegs: 141.58,
    projectedRevenuePerKentLeg: 61.96,
    projectedRoadHours: 181.03,
    assumedFleet: 4,
    operatingDaysPerWeek: 5,
    projectedRoadHoursPerVehicleDay: 9.05,
    assumedCostPerRoadHour: 50,
    projectedCost: 9051.49,
    projectedMarginPct: -3.19,
    topProgramVolumeSharePct: 26.37
  },
  gates: [
    {
      name: "Vehicle utilization",
      threshold: ">= 95%",
      value: "104.4%",
      status: "pass",
      confidence: "Tier 2",
      note:
        "Projected Kent-Legs divided by assumed weekly target capacity built from historical Kent-Legs per vehicle-day and a 4-vehicle, 5-day plan."
    },
    {
      name: "Billed utilization",
      threshold: ">= 105%",
      value: "100.0%",
      status: "provisional",
      confidence: "Tier 3",
      note:
        "Held provisional because the canonical billed-utilization formula is still unresolved across the source materials."
    },
    {
      name: "Total volume pool",
      threshold: ">= 120%",
      value: "115.4%",
      status: "provisional",
      confidence: "Tier 3",
      note:
        "Proxy based on requested trips versus completed trip base. The official pool logic remains underdefined."
    },
    {
      name: "Revenue per Kent-Leg",
      threshold: ">= $70",
      value: "$61.96",
      status: "fail",
      confidence: "Tier 2",
      note: "Projected weekly revenue divided by projected Kent-Legs."
    },
    {
      name: "Higher-acuity share",
      threshold: ">= 5%",
      value: "9.9%",
      status: "pass",
      confidence: "Tier 1",
      note: "Share of completed weekly trips in SecureCare or Stretcher Alternative lines."
    },
    {
      name: "Non-billable no-shows",
      threshold: "< 10%",
      value: "4.8%",
      status: "pass",
      confidence: "Tier 1",
      note:
        "Non-billable no-shows divided by completed trips plus billable and non-billable no-shows."
    },
    {
      name: "Road hours per vehicle per day",
      threshold: ">= 9.0",
      value: "9.05",
      status: "pass",
      confidence: "Tier 2",
      note: "Projected road hours divided by assumed fleet-days in a 4-vehicle, 5-day plan."
    },
    {
      name: "Contract concentration",
      threshold: "<= 20%",
      value: "26.4%",
      status: "fail",
      confidence: "Tier 2",
      note:
        "Proxy uses top program weekly volume share because the example intake is program-based rather than contract-keyed."
    },
    {
      name: "Cost per road hour",
      threshold: "<= $50",
      value: "$50.00",
      status: "pass",
      confidence: "Tier 2",
      note:
        "Held at the charter ceiling for MVP planning because regional cost detail is incomplete."
    }
  ],
  drivers: [
    {
      title: "Quality Volume",
      status: "fail",
      icon: "QV",
      metricLabel: "Quality mix",
      metricValue: "84.6%",
      threshold: ">= 90%",
      supportLabel: "Quality trips",
      supportValue: "77 of 91",
      detail:
        "The intake is still too dependent on non-quality filler and broker volume to satisfy the preferred launch mix."
    },
    {
      title: "Filler + Broker Buffer",
      status: "pass",
      icon: "FB",
      metricLabel: "Supplemental mix",
      metricValue: "15.4%",
      threshold: ">= 10%",
      supportLabel: "Programs represented",
      supportValue: "2 non-core lines",
      detail:
        "Overflow and referral programs create some buffer for midday utilization even though they do not repair revenue density."
    },
    {
      title: "Revenue Strength",
      status: "fail",
      icon: "RV",
      metricLabel: "Avg $ / Kent-Leg",
      metricValue: "$61.96",
      threshold: ">= $70.00",
      supportLabel: "Projected weekly revenue",
      supportValue: "$8,772",
      detail:
        "The current pricing and mix do not clear the charter revenue-density threshold."
    },
    {
      title: "Cost + Concentration",
      status: "fail",
      icon: "CR",
      metricLabel: "Top program share",
      metricValue: "26.4%",
      threshold: "<= 20%",
      supportLabel: "Cost / road hour",
      supportValue: "$50.00",
      detail:
        "Cost only clears the line because it is pinned to the ceiling assumption, while the program mix remains too concentrated."
    },
    {
      title: "Utilization",
      status: "provisional",
      icon: "UT",
      metricLabel: "Vehicle utilization",
      metricValue: "104.4%",
      threshold: ">= 95%",
      supportLabel: "Billed utilization",
      supportValue: "100.0% vs 105%",
      detail:
        "Physical utilization clears, but billed utilization stays provisional until the final source-of-truth formula is frozen."
    },
    {
      title: "Service Mix + Reliability",
      status: "pass",
      icon: "SR",
      metricLabel: "Higher-acuity share",
      metricValue: "9.9%",
      threshold: ">= 5%",
      supportLabel: "Non-billable no-shows",
      supportValue: "4.8% and 9.05 hrs/day",
      detail:
        "Higher-acuity services, no-show control, and road-hour density all land on the right side of the current thresholds."
    }
  ],
  intakePrograms: [
    {
      program: "Dialysis Transportation Program",
      volumeClass: "Quality",
      tripMode: "Wheelchair",
      weeklyTrips: 24,
      kentLegs: 37.0,
      avgRevenuePerKentLeg: 61.9,
      billedIndex: 1.125,
      scheduling: "Recurring · 72 hr lead"
    },
    {
      program: "ED / Inpatient Discharges - Ambulatory",
      volumeClass: "Quality",
      tripMode: "Ambulatory",
      weeklyTrips: 18,
      kentLegs: 26.8,
      avgRevenuePerKentLeg: 44.71,
      billedIndex: 1.111,
      scheduling: "Same-day · 12 hr lead"
    },
    {
      program: "ED / Inpatient Discharges - Wheelchair",
      volumeClass: "Quality",
      tripMode: "Wheelchair",
      weeklyTrips: 14,
      kentLegs: 20.9,
      avgRevenuePerKentLeg: 61.6,
      billedIndex: 1.143,
      scheduling: "Same-day · 12 hr lead"
    },
    {
      program: "Oncology & Specialist Recurring Appointments",
      volumeClass: "Quality",
      tripMode: "Ambulatory",
      weeklyTrips: 12,
      kentLegs: 20.0,
      avgRevenuePerKentLeg: 43.03,
      billedIndex: 1.083,
      scheduling: "Recurring · 48 hr lead"
    },
    {
      program: "Community Access Overflow",
      volumeClass: "Filler",
      tripMode: "Ambulatory",
      weeklyTrips: 8,
      kentLegs: 11.0,
      avgRevenuePerKentLeg: 42.23,
      billedIndex: 1.0,
      scheduling: "Recurring · 24 hr lead"
    },
    {
      program: "Overflow Facility Transfers via Network Referrals",
      volumeClass: "Broker",
      tripMode: "Wheelchair",
      weeklyTrips: 6,
      kentLegs: 8.3,
      avgRevenuePerKentLeg: 56.62,
      billedIndex: 1.0,
      scheduling: "Referral-based · 4 hr lead"
    },
    {
      program: "Interfacility Transfers - Stretcher Alternative",
      volumeClass: "Quality",
      tripMode: "Stretcher Alt",
      weeklyTrips: 5,
      kentLegs: 9.2,
      avgRevenuePerKentLeg: 121.76,
      billedIndex: 1.0,
      scheduling: "Scheduled · 8 hr lead"
    },
    {
      program: "Behavioral Health Secure Transport",
      volumeClass: "Quality",
      tripMode: "SecureCare",
      weeklyTrips: 4,
      kentLegs: 8.4,
      avgRevenuePerKentLeg: 128.21,
      billedIndex: 1.25,
      scheduling: "Secure handoff · 6 hr lead"
    }
  ],
  assumptions: [
    {
      title: "Fleet plan",
      source: "market.fleet · market.operating_days_per_week",
      detail:
        "The operating plan assumed for this market: how many vehicles and how many active days per week we size the fleet for. Used as the denominator for vehicle utilization, road-hours per vehicle-day, and billed utilization."
    },
    {
      title: "Kent-Leg conversion (v2 planning formula)",
      source: "kent_leg_planning_v2 × mode_multipliers",
      detail:
        "A Kent-Leg is our normalized trip unit so we can compare wheelchair, ambulatory, stretcher, and SecureCare work on the same axis. The \"v2 planning formula\" is the second-pass version we use for forward-looking planning: each trip is multiplied by a mode-specific weight (for example stretcher and SecureCare carry heavier multipliers than a standard ambulatory run) and summed into a weekly Kent-Leg total. It is in place because the v1 constants that finance shipped did not separate acuity; we will switch back to a single audited formula once the official Kent-Leg definition is locked."
    },
    {
      title: "Cost basis",
      source: "charter.cost_per_road_hour_ceiling",
      detail:
        "Projected hourly cost is pinned to the charter ceiling until regional cost detail (driver wage, fuel, overhead, operating) can be validated for this corridor. Because cost is capped rather than measured, the cost-per-road-hour gate clears automatically; treat its pass as provisional."
    },
    {
      title: "Concentration proxy",
      source: "intake.programs[].weekly_volume_share",
      detail:
        "The launch charter caps concentration by contract. The example workbook is program-keyed (one intake row per program, not per contract), so we report the top program's share of weekly volume as a proxy for contract concentration until contract-level keys exist."
    }
  ],
  riskActions: [
    {
      owner: "Contracting",
      title: "Lift revenue density above $70 / Kent-Leg",
      detail:
        "Reprice ambulatory and dialysis lines or shift more demand into higher-acuity services with stronger unit economics.",
      due: "2026-04-29",
      status: "Not Started"
    },
    {
      owner: "Sales",
      title: "Reduce program concentration below 20%",
      detail:
        "Add at least one new quality-volume line or diversify the dialysis-heavy mix before launch approval.",
      due: "2026-04-29",
      status: "Not Started"
    },
    {
      owner: "Finance",
      title: "Freeze the billed-utilization formula",
      detail:
        "Resolve the canonical billed-utilization denominator so the provisional gate can convert to an audited result.",
      due: "2026-04-22",
      status: "In Progress"
    },
    {
      owner: "Operations",
      title: "Replace the cost ceiling with local coefficients",
      detail:
        "Swap the flat $50 road-hour assumption for verified market-level driver, fuel, overhead, and operating costs.",
      due: "2026-05-06",
      status: "Not Started"
    }
  ]
} as const
