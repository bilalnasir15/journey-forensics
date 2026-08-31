"use client";

import {
  Activity,
  ArrowUpRight,
  BarChart3,
  BrainCircuit,
  Database,
  Gauge,
  Layers3,
  Search,
  ShieldAlert,
  Users,
  UploadCloud,
} from "lucide-react";

import { motion } from "motion/react";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import Link from "next/link";

import {
  getHealth,
  getKPIs,
  type KPIResponse,
} from "@/lib/api";

// ============================================================
// MODULES
// ============================================================

const modules = [
  {
    title: "Customer Intelligence",
    description:
      "Profiles, behavioral segments, cohorts and customer patterns.",
    icon: Users,
    href: "/customers",
  },

  {
    title: "Journey Forensics",
    description:
      "Trace booking journeys, payment friction and anomalies.",
    icon: Search,
    href: "/journeys",
  },

  {
    title: "KPI Intelligence",
    description:
      "Monitor validated business metrics from the analytics layer.",
    icon: Gauge,
    href: "/kpis",
  },

  {
    title: "Investigation Engine",
    description:
      "Investigate metrics, thresholds and suspicious journeys.",
    icon: BrainCircuit,
    href: "#investigation",
  },
];

// ============================================================
// KPI LOOKUP
// ============================================================

function findKPI(
  data: KPIResponse | null,
  name: string
): number | null {
  if (!data) {
    return null;
  }

  return (
    data.kpis.find(
      (kpi) =>
        kpi.kpi_name === name
    )?.value ?? null
  );
}

// ============================================================
// HOME
// ============================================================

export default function Home() {
  const [kpis, setKpis] =
    useState<KPIResponse | null>(
      null
    );

  const [apiOnline, setApiOnline] =
    useState(false);

  const [loading, setLoading] =
    useState(true);

  const [error, setError] =
    useState<string | null>(
      null
    );

  // ==========================================================
  // LOAD
  // ==========================================================

  useEffect(() => {
    let active = true;

    async function loadData() {
      try {
        setLoading(true);

        const [
          health,
          kpiData,
        ] = await Promise.all([
          getHealth(),
          getKPIs(),
        ]);

        if (!active) {
          return;
        }

        setApiOnline(
          health.status ===
            "healthy"
        );

        setKpis(
          kpiData
        );

        setError(null);
      } catch (err) {
        if (!active) {
          return;
        }

        setApiOnline(false);

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load API data."
        );
      } finally {
        if (active) {
          setLoading(false);
        }
      }
    }

    loadData();

    return () => {
      active = false;
    };
  }, []);

  // ==========================================================
  // KPI VALUES
  // ==========================================================

  const customerCount =
    findKPI(
      kpis,
      "TOTAL_CUSTOMERS"
    );

  const bookingCount =
    findKPI(
      kpis,
      "TOTAL_BOOKINGS"
    );

  const revenue =
    findKPI(
      kpis,
      "TOTAL_REVENUE"
    );

  const anomalyRate =
    findKPI(
      kpis,
      "ANOMALY_RATE"
    );

  const averageJourneyDuration =
    findKPI(
      kpis,
      "AVERAGE_JOURNEY_DURATION"
    );

  const averageFrictionScore =
    findKPI(
      kpis,
      "AVERAGE_FRICTION_SCORE"
    );

  // ==========================================================
  // STATS
  // ==========================================================

  const stats = useMemo(() => {
    return [
      {
        label: "Customers",
        value:
          loading
            ? "..."
            : customerCount !==
                null
              ? customerCount.toLocaleString()
              : "—",
        change:
          apiOnline
            ? "Live API"
            : "Unavailable",
        icon: Users,
        href: "/customers",
      },

      {
        label: "Bookings",
        value:
          loading
            ? "..."
            : bookingCount !==
                null
              ? bookingCount.toLocaleString()
              : "—",
        change:
          apiOnline
            ? "Live API"
            : "Unavailable",
        icon: BarChart3,
        href: "/journeys",
      },

      {
        label: "Revenue",
        value:
          loading
            ? "..."
            : revenue !==
                null
              ? `${(
                  revenue /
                  1_000_000
                ).toFixed(
                  2
                )}M`
              : "—",
        change:
          apiOnline
            ? "Live API"
            : "Unavailable",
        icon: Database,
        href: "/kpis",
      },

      {
        label: "Anomaly Rate",
        value:
          loading
            ? "..."
            : anomalyRate !==
                null
              ? `${(
                  anomalyRate *
                  100
                ).toFixed(
                  2
                )}%`
              : "—",
        change:
          anomalyRate !==
            null &&
          anomalyRate >
            0.3
            ? "Requires attention"
            : "Monitored",
        icon: ShieldAlert,
        href: "/journeys",
      },
    ];
  }, [
    loading,
    apiOnline,
    customerCount,
    bookingCount,
    revenue,
    anomalyRate,
  ]);

  return (
    <main className="min-h-screen overflow-hidden bg-[#07111f] text-white">

      {/* ======================================================
          BACKGROUND
          ====================================================== */}

      <div className="pointer-events-none fixed inset-0 overflow-hidden">

        <motion.div
          className="absolute -left-32 -top-32 h-96 w-96 rounded-full bg-cyan-400/10 blur-3xl"
          animate={{
            x: [0, 80, 0],
            y: [0, 40, 0],
            scale: [1, 1.15, 1],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        <motion.div
          className="absolute right-[-150px] top-1/4 h-[30rem] w-[30rem] rounded-full bg-blue-500/10 blur-3xl"
          animate={{
            x: [0, -70, 0],
            y: [0, 70, 0],
            scale: [1, 1.12, 1],
          }}
          transition={{
            duration: 13,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_top,rgba(59,130,246,0.08),transparent_40%)]" />
      </div>

      {/* ======================================================
          NAVIGATION
          ====================================================== */}

      <nav className="relative z-10 border-b border-white/10 bg-[#07111f]/70 backdrop-blur-xl">

        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">

          <Link
            href="/"
            className="flex items-center gap-3"
          >

            <motion.div
              className="flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10"
              whileHover={{
                rotate: 8,
                scale: 1.05,
              }}
            >
              <Layers3 className="h-5 w-5 text-cyan-300" />
            </motion.div>

            <div>
              <p className="text-sm font-semibold tracking-[0.22em]">
                JOURNEY
              </p>

              <p className="text-xs tracking-[0.3em] text-cyan-300/70">
                FORENSICS
              </p>
            </div>

          </Link>

          <div className="hidden items-center gap-8 md:flex">

            <Link
              href="/"
              className="text-sm text-white"
            >
              Overview
            </Link>

            <Link
              href="/customers"
              className="text-sm text-white/50 transition hover:text-white"
            >
              Customers
            </Link>

            <Link
              href="/journeys"
              className="text-sm text-white/50 transition hover:text-white"
            >
              Journeys
            </Link>

            <Link
              href="/kpis"
              className="text-sm text-white/50 transition hover:text-white"
            >
              KPIs
            </Link>

            <Link
              href="#investigation"
              className="text-sm text-white/50 transition hover:text-white"
            >
              Investigate
            </Link>

          </div>

          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-white/60">

            <span
              className={`h-2 w-2 rounded-full ${
                loading
                  ? "animate-pulse bg-amber-300"
                  : apiOnline
                    ? "bg-emerald-400"
                    : "bg-red-400"
              }`}
            />

            {loading
              ? "Synchronizing"
              : apiOnline
                ? "API Connected"
                : "API Offline"}

          </div>
        </div>
      </nav>

      {/* ======================================================
          HERO
          ====================================================== */}

      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-12 pt-16">

        <motion.div
          initial={{
            opacity: 0,
            y: 20,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            duration: 0.7,
          }}
          className="max-w-4xl"
        >

          <div className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-white/60 backdrop-blur-xl">

            <span
              className={`h-2 w-2 rounded-full ${
                loading
                  ? "animate-pulse bg-amber-300"
                  : apiOnline
                    ? "bg-emerald-400"
                    : "bg-red-400"
              }`}
            />

            {loading
              ? "Synchronizing with analytics engine"
              : apiOnline
                ? "Live analytics engine online"
                : "Analytics engine unavailable"}

          </div>

          <h1 className="text-5xl font-semibold leading-[1.05] tracking-tight sm:text-6xl lg:text-7xl">

            Turn customer journeys into

            <span className="block bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400 bg-clip-text text-transparent">
              forensic intelligence.
            </span>

          </h1>

          <p className="mt-6 max-w-2xl text-lg leading-8 text-white/55">

            Journey Forensics connects customer behavior,
            booking journeys, payment friction, anomalies,
            segmentation and investigation into one
            analytical experience.

          </p>

          {error && (
            <div className="mt-5 max-w-2xl rounded-2xl border border-red-300/10 bg-red-300/5 px-4 py-3 text-sm text-red-200/80">
              {error}
            </div>
          )}

          <div className="mt-8 flex flex-wrap gap-4">

            <Link href="/journeys">
              <motion.div
                className="group flex items-center gap-2 rounded-2xl bg-cyan-300 px-5 py-3 font-medium text-[#07111f]"
                whileHover={{
                  scale: 1.03,
                }}
                whileTap={{
                  scale: 0.98,
                }}
              >
                Explore journeys

                <ArrowUpRight className="h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />
              </motion.div>
            </Link>

            <Link href="/upload">

              <motion.div
                className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-white/75 backdrop-blur-xl transition hover:bg-white/10"
                whileTap={{
                  scale: 0.98,
                }}
              >
                <UploadCloud className="h-4 w-4" />
                Upload data
              </motion.div>

            </Link>

          </div>

        </motion.div>

      </section>

      {/* ======================================================
          KPI CARDS
          ====================================================== */}

      <section className="relative z-10 mx-auto grid max-w-7xl gap-4 px-6 md:grid-cols-2 xl:grid-cols-4">

        {stats.map(
          (
            stat,
            index
          ) => {

            const Icon =
              stat.icon;

            return (
              <Link
                href={
                  stat.href
                }
                key={
                  stat.label
                }
              >

                <motion.div
                  initial={{
                    opacity: 0,
                    y: 25,
                  }}
                  animate={{
                    opacity: 1,
                    y: 0,
                  }}
                  transition={{
                    delay:
                      0.15 +
                      index *
                        0.08,
                    duration: 0.55,
                  }}
                  whileHover={{
                    y: -5,
                  }}
                  className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/[0.045] p-6 backdrop-blur-xl"
                >

                  <div className="absolute inset-0 bg-gradient-to-br from-white/[0.06] to-transparent opacity-0 transition group-hover:opacity-100" />

                  <div className="relative">

                    <div className="mb-8 flex items-center justify-between">

                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/5">

                        <Icon className="h-5 w-5 text-cyan-300" />

                      </div>

                      <ArrowUpRight className="h-4 w-4 text-white/20 transition group-hover:text-white/60" />

                    </div>

                    <p className="text-sm text-white/45">
                      {stat.label}
                    </p>

                    <p className="mt-2 text-3xl font-semibold">
                      {stat.value}
                    </p>

                    <p
                      className={`mt-2 text-xs ${
                        stat.label ===
                          "Anomaly Rate" &&
                        anomalyRate !==
                          null &&
                        anomalyRate >
                          0.3
                          ? "text-amber-300/80"
                          : "text-emerald-300/70"
                      }`}
                    >
                      {stat.change}
                    </p>

                  </div>

                </motion.div>

              </Link>
            );
          }
        )}

      </section>

      {/* ======================================================
          JOURNEY HEALTH
          ====================================================== */}

      <section
        id="journeys"
        className="relative z-10 mx-auto max-w-7xl px-6 py-12"
      >

        <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">

          <Link href="/journeys">

            <motion.div
              initial={{
                opacity: 0,
                x: -25,
              }}
              animate={{
                opacity: 1,
                x: 0,
              }}
              transition={{
                delay: 0.35,
              }}
              whileHover={{
                y: -3,
              }}
              className="rounded-[2rem] border border-white/10 bg-white/[0.045] p-7 backdrop-blur-xl"
            >

              <div className="flex items-start justify-between">

                <div>

                  <div className="flex items-center gap-2 text-sm text-white/45">

                    <Activity className="h-4 w-4 text-cyan-300" />

                    Journey intelligence

                  </div>

                  <h2 className="mt-2 text-2xl font-semibold">
                    Customer journey health
                  </h2>

                </div>

                <div className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs text-emerald-200">
                  {apiOnline
                    ? "LIVE"
                    : "OFFLINE"}
                </div>

              </div>

              <div className="mt-10 h-56 rounded-3xl border border-white/5 bg-black/10 p-6">

                <div className="flex h-full items-end gap-3">

                  {[
                    38,
                    55,
                    48,
                    68,
                    58,
                    76,
                    63,
                    84,
                    72,
                    91,
                    79,
                    88,
                  ].map(
                    (
                      height,
                      index
                    ) => (

                      <motion.div
                        key={
                          index
                        }
                        initial={{
                          height: 0,
                        }}
                        animate={{
                          height:
                            `${height}%`,
                        }}
                        transition={{
                          delay:
                            0.5 +
                            index *
                              0.04,
                          duration: 0.7,
                        }}
                        className="flex-1 rounded-t-xl bg-gradient-to-t from-blue-500/30 via-cyan-300/60 to-cyan-200"
                      />

                    )
                  )}

                </div>

              </div>

              <div className="mt-5 grid grid-cols-3 gap-3">

                <div className="rounded-2xl bg-white/[0.035] p-4">

                  <p className="text-xs text-white/35">
                    Avg. duration
                  </p>

                  <p className="mt-1 text-xl font-semibold">
                    {averageJourneyDuration !==
                    null
                      ? `${averageJourneyDuration.toFixed(
                          2
                        )}m`
                      : "—"}
                  </p>

                </div>

                <div className="rounded-2xl bg-white/[0.035] p-4">

                  <p className="text-xs text-white/35">
                    Avg. friction
                  </p>

                  <p className="mt-1 text-xl font-semibold">
                    {averageFrictionScore !==
                    null
                      ? averageFrictionScore.toFixed(
                          2
                        )
                      : "—"}
                  </p>

                </div>

                <div className="rounded-2xl bg-white/[0.035] p-4">

                  <p className="text-xs text-white/35">
                    Anomaly rate
                  </p>

                  <p className="mt-1 text-xl font-semibold text-red-300">
                    {anomalyRate !==
                    null
                      ? `${(
                          anomalyRate *
                          100
                        ).toFixed(
                          2
                        )}%`
                      : "—"}
                  </p>

                </div>

              </div>

            </motion.div>

          </Link>

          <motion.div
            id="investigation"
            initial={{
              opacity: 0,
              x: 25,
            }}
            animate={{
              opacity: 1,
              x: 0,
            }}
            transition={{
              delay: 0.45,
            }}
            className="rounded-[2rem] border border-red-300/10 bg-red-300/[0.035] p-7 backdrop-blur-xl"
          >

            <div className="flex items-center gap-2 text-sm text-red-200/70">

              <ShieldAlert className="h-4 w-4" />

              Investigation queue

            </div>

            <h2 className="mt-2 text-2xl font-semibold">
              Attention required
            </h2>

            <div className="mt-7 space-y-3">

              {[
                [
                  "Payment retry storm",
                  "High",
                ],
                [
                  "Multiple payment failures",
                  "Critical",
                ],
                [
                  "Unresolved booking",
                  "Critical",
                ],
              ].map(
                (
                  [title, level],
                  index
                ) => (

                  <Link
                    href="/journeys"
                    key={
                      title
                    }
                  >

                    <motion.div
                      initial={{
                        opacity: 0,
                        x: 10,
                      }}
                      animate={{
                        opacity: 1,
                        x: 0,
                      }}
                      transition={{
                        delay:
                          0.7 +
                          index *
                            0.1,
                      }}
                      whileHover={{
                        x: 4,
                      }}
                      className="flex items-center justify-between rounded-2xl border border-white/5 bg-black/10 p-4"
                    >

                      <div>

                        <p className="text-sm font-medium">
                          {title}
                        </p>

                        <p className="mt-1 text-xs text-white/35">
                          Investigation signal detected
                        </p>

                      </div>

                      <span
                        className={`rounded-full px-3 py-1 text-[10px] font-medium uppercase tracking-wider ${
                          level ===
                          "Critical"
                            ? "bg-red-400/10 text-red-200"
                            : "bg-amber-300/10 text-amber-200"
                        }`}
                      >
                        {level}
                      </span>

                    </motion.div>

                  </Link>

                )
              )}

            </div>

            <Link
              href="/journeys"
              className="mt-5 flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/55 transition hover:bg-white/10 hover:text-white"
            >

              Open journey investigation

              <ArrowUpRight className="h-4 w-4" />

            </Link>

          </motion.div>

        </div>

      </section>

      {/* ======================================================
          MODULES
          ====================================================== */}

      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-20">

        <div className="mb-6">

          <p className="text-sm text-cyan-300/70">
            Intelligence modules
          </p>

          <h2 className="mt-2 text-3xl font-semibold">
            Explore the platform
          </h2>

        </div>

        <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">

          {modules.map(
            (
              module,
              index
            ) => {

              const Icon =
                module.icon;

              return (
                <Link
                  href={
                    module.href
                  }
                  key={
                    module.title
                  }
                >

                  <motion.div
                    initial={{
                      opacity: 0,
                      y: 20,
                    }}
                    animate={{
                      opacity: 1,
                      y: 0,
                    }}
                    transition={{
                      delay:
                        0.8 +
                        index *
                          0.08,
                    }}
                    whileHover={{
                      y: -6,
                    }}
                    className="group h-full rounded-3xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl"
                  >

                    <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/5">

                      <Icon className="h-5 w-5 text-cyan-300" />

                    </div>

                    <h3 className="mt-6 font-semibold">
                      {module.title}
                    </h3>

                    <p className="mt-2 text-sm leading-6 text-white/40">
                      {module.description}
                    </p>

                    <div className="mt-6 flex items-center gap-2 text-xs text-white/35 transition group-hover:text-cyan-200">

                      Explore

                      <ArrowUpRight className="h-3.5 w-3.5" />

                    </div>

                  </motion.div>

                </Link>
              );
            }
          )}

        </div>

      </section>

      {/* ======================================================
          FOOTER
          ====================================================== */}

      <footer className="relative z-10 border-t border-white/10 px-6 py-6">

        <div className="mx-auto flex max-w-7xl flex-col justify-between gap-3 text-xs text-white/25 sm:flex-row">

          <p>
            Journey Forensics
          </p>

          <p>
            Live analytical intelligence platform
          </p>

        </div>

      </footer>

    </main>
  );
}