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
// FORENSIC BACKGROUND MARKERS
// ============================================================

const FORENSIC_POINTS = [
  {
    left: "8%",
    top: "17%",
    size: 3,
    delay: 0,
    duration: 5.5,
  },
  {
    left: "18%",
    top: "72%",
    size: 4,
    delay: 1.2,
    duration: 6.5,
  },
  {
    left: "29%",
    top: "28%",
    size: 2,
    delay: 0.7,
    duration: 7,
  },
  {
    left: "41%",
    top: "82%",
    size: 3,
    delay: 1.8,
    duration: 5.8,
  },
  {
    left: "53%",
    top: "18%",
    size: 4,
    delay: 0.4,
    duration: 6.8,
  },
  {
    left: "64%",
    top: "66%",
    size: 2,
    delay: 1.5,
    duration: 5.2,
  },
  {
    left: "74%",
    top: "31%",
    size: 3,
    delay: 0.8,
    duration: 6.2,
  },
  {
    left: "83%",
    top: "77%",
    size: 4,
    delay: 1.9,
    duration: 7.2,
  },
  {
    left: "91%",
    top: "20%",
    size: 2,
    delay: 0.3,
    duration: 5.7,
  },
  {
    left: "47%",
    top: "52%",
    size: 2,
    delay: 1.1,
    duration: 6.4,
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

        accent: "cyan",
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

        accent: "blue",
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

        accent: "violet",
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

        accent: "danger",
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

    <main className="relative min-h-screen overflow-hidden bg-[#07111f] text-white">


      {/* ======================================================
          FORENSIC BACKGROUND SYSTEM
          ====================================================== */}

      <div
        className="pointer-events-none fixed inset-0 overflow-hidden"
        aria-hidden="true"
      >

        {/* BASE ATMOSPHERE */}

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_50%_0%,rgba(56,189,248,0.045),transparent_35%),radial-gradient(circle_at_90%_60%,rgba(139,92,246,0.055),transparent_35%)]" />


        {/* CYAN FIELD */}

        <motion.div
          className="absolute -left-44 -top-44 h-[34rem] w-[34rem] rounded-full bg-cyan-400/[0.08] blur-3xl"
          animate={{
            x: [
              0,
              90,
              0,
            ],

            y: [
              0,
              45,
              0,
            ],

            scale: [
              1,
              1.14,
              1,
            ],
          }}
          transition={{
            duration: 13,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />


        {/* VIOLET FIELD */}

        <motion.div
          className="absolute right-[-180px] top-[22%] h-[38rem] w-[38rem] rounded-full bg-violet-500/[0.075] blur-3xl"
          animate={{
            x: [
              0,
              -85,
              0,
            ],

            y: [
              0,
              60,
              0,
            ],

            scale: [
              1,
              1.12,
              1,
            ],
          }}
          transition={{
            duration: 16,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />


        {/* FORENSIC GRID */}

        <div
          className="absolute inset-0 opacity-[0.055]"
          style={{
            backgroundImage: `
              linear-gradient(
                rgba(103,232,249,0.22) 1px,
                transparent 1px
              ),
              linear-gradient(
                90deg,
                rgba(103,232,249,0.22) 1px,
                transparent 1px
              )
            `,
            backgroundSize:
              "72px 72px",
            maskImage:
              "radial-gradient(circle at center, black 20%, transparent 85%)",
            WebkitMaskImage:
              "radial-gradient(circle at center, black 20%, transparent 85%)",
          }}
        />


        {/* SCAN LINE */}

        <motion.div
          className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-cyan-300/25 to-transparent"
          animate={{
            top: [
              "8%",
              "88%",
              "8%",
            ],
          }}
          transition={{
            duration: 18,
            repeat: Infinity,
            ease: "linear",
          }}
        />


        <motion.div
          className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-violet-300/20 to-transparent"
          animate={{
            top: [
              "78%",
              "18%",
              "78%",
            ],
          }}
          transition={{
            duration: 23,
            repeat: Infinity,
            ease: "linear",
          }}
        />


        {/* CYAN RADAR */}

        <div className="absolute left-[12%] top-[42%] hidden h-72 w-72 md:block">

          <motion.div
            className="absolute inset-0 rounded-full border border-cyan-300/[0.08]"
            animate={{
              scale: [
                0.82,
                1.08,
                0.82,
              ],

              opacity: [
                0.2,
                0.6,
                0.2,
              ],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          <motion.div
            className="absolute inset-8 rounded-full border border-cyan-300/[0.07]"
            animate={{
              scale: [
                1.05,
                0.8,
                1.05,
              ],
            }}
            transition={{
              duration: 9,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          <motion.div
            className="absolute inset-[22%] rounded-full border border-cyan-300/[0.08]"
            animate={{
              rotate: 360,
            }}
            transition={{
              duration: 28,
              repeat: Infinity,
              ease: "linear",
            }}
          >

            <span className="absolute -right-1 top-1/2 h-2 w-2 rounded-full bg-cyan-300/50 shadow-[0_0_14px_rgba(103,232,249,0.45)]" />

          </motion.div>


          <div className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-300/40 shadow-[0_0_18px_rgba(103,232,249,0.5)]" />

        </div>


        {/* VIOLET RADAR */}

        <div className="absolute right-[8%] top-[20%] hidden h-80 w-80 lg:block">

          <motion.div
            className="absolute inset-0 rounded-full border border-violet-300/[0.07]"
            animate={{
              scale: [
                0.78,
                1.05,
                0.78,
              ],

              opacity: [
                0.18,
                0.5,
                0.18,
              ],
            }}
            transition={{
              duration: 10,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          <motion.div
            className="absolute inset-10 rounded-full border border-violet-300/[0.06]"
            animate={{
              rotate: -360,
            }}
            transition={{
              duration: 34,
              repeat: Infinity,
              ease: "linear",
            }}
          />

          <motion.div
            className="absolute inset-[28%] rounded-full border border-violet-300/[0.06]"
            animate={{
              scale: [
                1,
                0.75,
                1,
              ],
            }}
            transition={{
              duration: 7,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          >

            <span className="absolute -left-1 top-1/2 h-2 w-2 rounded-full bg-violet-300/50 shadow-[0_0_14px_rgba(167,139,250,0.45)]" />

          </motion.div>

        </div>


        {/* FLOATING EVIDENCE POINTS */}

        {FORENSIC_POINTS.map(
          (
            point,
            index
          ) => (

            <motion.span
              key={index}
              className="absolute rounded-full bg-cyan-200/40 shadow-[0_0_10px_rgba(103,232,249,0.28)]"
              style={{
                left:
                  point.left,
                top:
                  point.top,
                width:
                  point.size,
                height:
                  point.size,
              }}
              animate={{
                y: [
                  0,
                  -14,
                  0,
                ],

                x: [
                  0,
                  index % 2 ===
                    0
                    ? 7
                    : -7,
                  0,
                ],

                opacity: [
                  0.15,
                  0.65,
                  0.15,
                ],

                scale: [
                  0.8,
                  1.15,
                  0.8,
                ],
              }}
              transition={{
                duration:
                  point.duration,
                delay:
                  point.delay,
                repeat:
                  Infinity,
                ease: "easeInOut",
              }}
            />

          )
        )}


        {/* CROSSHAIRS */}

        <div className="absolute left-[6%] top-[58%] hidden h-8 w-8 opacity-20 lg:block">

          <span className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-cyan-300/50" />

          <span className="absolute left-0 top-1/2 h-px w-full -translate-y-1/2 bg-cyan-300/50" />

          <span className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-300/60" />

        </div>


        <div className="absolute right-[6%] bottom-[20%] hidden h-8 w-8 opacity-15 lg:block">

          <span className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-violet-300/50" />

          <span className="absolute left-0 top-1/2 h-px w-full -translate-y-1/2 bg-violet-300/50" />

          <span className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full border border-violet-300/60" />

        </div>


        {/* VIGNETTE */}

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_35%,rgba(3,10,20,0.24)_100%)]" />

      </div>


      {/* ======================================================
          NAVIGATION
          ====================================================== */}

      <nav className="relative z-20 border-b border-white/10 bg-[#07111f]/70 backdrop-blur-xl">

        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">

          <Link
            href="/"
            className="group flex items-center gap-3"
          >

            <motion.div
              className="flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10 shadow-[0_0_25px_rgba(103,232,249,0.06)]"
              whileHover={{
                rotate: 8,
                scale: 1.05,
              }}
              transition={{
                duration: 0.2,
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


          <div className="flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-white/60 backdrop-blur-xl">

            <motion.span
              className={`h-2 w-2 rounded-full ${
                loading
                  ? "bg-amber-300"
                  : apiOnline
                    ? "bg-emerald-400"
                    : "bg-red-400"
              }`}
              animate={{
                opacity: [
                  0.45,
                  1,
                  0.45,
                ],
              }}
              transition={{
                duration: 1.8,
                repeat: Infinity,
                ease: "easeInOut",
              }}
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

      <section className="relative z-10 mx-auto max-w-7xl px-6 pb-14 pt-16">

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

          <motion.div
            initial={{
              opacity: 0,
              scale: 0.96,
            }}
            animate={{
              opacity: 1,
              scale: 1,
            }}
            transition={{
              delay: 0.1,
              duration: 0.45,
            }}
            className="mb-5 inline-flex items-center gap-2 rounded-full border border-white/10 bg-white/5 px-4 py-2 text-xs text-white/60 shadow-[0_0_22px_rgba(103,232,249,0.025)] backdrop-blur-xl"
          >

            <motion.span
              className={`h-2 w-2 rounded-full ${
                loading
                  ? "bg-amber-300"
                  : apiOnline
                    ? "bg-emerald-400"
                    : "bg-red-400"
              }`}
              animate={{
                scale: [
                  0.8,
                  1.15,
                  0.8,
                ],
              }}
              transition={{
                duration: 1.7,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />

            {loading
              ? "Synchronizing with analytics engine"
              : apiOnline
                ? "Live analytics engine online"
                : "Analytics engine unavailable"}

          </motion.div>


          <h1 className="text-5xl font-semibold leading-[1.05] tracking-tight sm:text-6xl lg:text-7xl">

            Turn customer journeys into

            <motion.span
              className="block bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400 bg-clip-text text-transparent"
              animate={{
                opacity: [
                  0.88,
                  1,
                  0.88,
                ],
              }}
              transition={{
                duration: 4,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            >
              forensic intelligence.
            </motion.span>

          </h1>


          <p className="mt-6 max-w-2xl text-lg leading-8 text-white/55">

            Journey Forensics connects customer behavior,
            booking journeys, payment friction, anomalies,
            segmentation and investigation into one
            analytical experience.

          </p>


          {error && (

            <motion.div
              initial={{
                opacity: 0,
                y: 8,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              className="mt-5 max-w-2xl rounded-2xl border border-red-300/10 bg-red-300/5 px-4 py-3 text-sm text-red-200/80"
            >

              {error}

            </motion.div>

          )}


          <div className="mt-8 flex flex-wrap gap-4">

            <Link href="/journeys">

              <motion.div
                className="group relative flex items-center gap-2 overflow-hidden rounded-2xl bg-cyan-300 px-5 py-3 font-medium text-[#07111f]"
                whileHover={{
                  scale: 1.035,
                  boxShadow:
                    "0 0 38px rgba(103,232,249,0.16)",
                }}
                whileTap={{
                  scale: 0.98,
                }}
              >

                <motion.span
                  className="absolute inset-y-0 left-[-30%] w-[25%] bg-white/25 blur-md"
                  animate={{
                    x: [
                      "-120%",
                      "520%",
                    ],
                  }}
                  transition={{
                    duration: 2.8,
                    repeat: Infinity,
                    repeatDelay: 2.5,
                    ease: "easeInOut",
                  }}
                />

                <span className="relative">
                  Explore journeys
                </span>

                <ArrowUpRight className="relative h-4 w-4 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />

              </motion.div>

            </Link>


            <Link href="/upload">

              <motion.div
                className="flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-white/75 backdrop-blur-xl transition hover:border-cyan-300/15 hover:bg-white/10"
                whileTap={{
                  scale: 0.98,
                }}
              >

                <UploadCloud className="h-4 w-4 text-cyan-300/80" />

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
                    y: 28,
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
                    y: -7,
                    scale: 1.012,
                  }}
                  className="group relative overflow-hidden rounded-3xl border border-white/10 bg-white/[0.045] p-6 shadow-[0_12px_35px_rgba(0,0,0,0.08)] backdrop-blur-xl"
                >

                  {/* CARD GLOW */}

                  <div className="pointer-events-none absolute -right-12 -top-12 h-32 w-32 rounded-full bg-cyan-300/[0.05] blur-3xl transition duration-500 group-hover:bg-cyan-300/[0.10]" />


                  {/* MOVING SHEEN */}

                  <motion.div
                    className="pointer-events-none absolute inset-y-0 left-[-45%] w-[22%] bg-gradient-to-r from-transparent via-white/[0.055] to-transparent blur-sm"
                    animate={{
                      x: [
                        "-120%",
                        "620%",
                      ],
                    }}
                    transition={{
                      duration: 5.8,
                      repeat: Infinity,
                      repeatDelay:
                        4 +
                        index,
                      ease: "easeInOut",
                    }}
                  />


                  <div className="relative">

                    <div className="mb-8 flex items-center justify-between">

                      <motion.div
                        whileHover={{
                          rotate: 6,
                          scale: 1.08,
                        }}
                        className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/5 bg-white/5"
                      >

                        <Icon className="h-5 w-5 text-cyan-300" />

                      </motion.div>


                      <ArrowUpRight className="h-4 w-4 text-white/20 transition duration-300 group-hover:-translate-y-0.5 group-hover:translate-x-0.5 group-hover:text-cyan-200/70" />

                    </div>


                    <p className="text-sm text-white/45">
                      {stat.label}
                    </p>


                    <motion.p
                      key={
                        stat.value
                      }
                      initial={{
                        opacity: 0,
                        y: 5,
                      }}
                      animate={{
                        opacity: 1,
                        y: 0,
                      }}
                      transition={{
                        duration:
                          0.35,
                      }}
                      className="mt-2 text-3xl font-semibold tracking-tight"
                    >

                      {stat.value}

                    </motion.p>


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


                    {/* BOTTOM PROGRESS LINE */}

                    <div className="mt-5 h-px overflow-hidden bg-white/5">

                      <motion.div
                        className="h-full bg-gradient-to-r from-cyan-300/40 via-blue-300/40 to-transparent"
                        initial={{
                          width: "0%",
                        }}
                        animate={{
                          width:
                            "72%",
                        }}
                        transition={{
                          delay:
                            0.55 +
                            index *
                              0.08,
                          duration:
                            0.8,
                          ease: "easeOut",
                        }}
                      />

                    </div>

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
        className="relative z-10 mx-auto max-w-7xl px-6 py-14"
      >

        <div className="grid gap-5 lg:grid-cols-[1.5fr_1fr]">


          {/* JOURNEY HEALTH */}

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
                y: -4,
              }}
              className="group relative overflow-hidden rounded-[2rem] border border-white/10 bg-white/[0.045] p-7 shadow-[0_18px_45px_rgba(0,0,0,0.10)] backdrop-blur-xl"
            >

              {/* CARD ATMOSPHERE */}

              <div className="pointer-events-none absolute -right-20 top-0 h-40 w-40 rounded-full bg-cyan-300/[0.045] blur-3xl transition duration-500 group-hover:bg-cyan-300/[0.08]" />


              <div className="relative">

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


                  <motion.div
                    whileHover={{
                      scale: 1.05,
                    }}
                    className="rounded-full border border-emerald-300/20 bg-emerald-300/10 px-3 py-1 text-xs text-emerald-200"
                  >

                    {apiOnline
                      ? "LIVE"
                      : "OFFLINE"}

                  </motion.div>

                </div>


                {/* CHART */}

                <div className="mt-10 h-56 rounded-3xl border border-white/5 bg-black/10 p-6">

                  <div className="relative flex h-full items-end gap-3">

                    {/* HORIZONTAL GRID */}

                    <div className="pointer-events-none absolute inset-0 flex flex-col justify-between py-1 opacity-40">

                      <span className="h-px w-full bg-white/5" />
                      <span className="h-px w-full bg-white/5" />
                      <span className="h-px w-full bg-white/5" />
                      <span className="h-px w-full bg-white/5" />

                    </div>


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
                            ease:
                              "easeOut",
                          }}
                          whileHover={{
                            scaleY:
                              1.06,
                            filter:
                              "brightness(1.16)",
                          }}
                          style={{
                            transformOrigin:
                              "bottom",
                          }}
                          className="group/bar relative z-10 flex-1 cursor-pointer rounded-t-xl bg-gradient-to-t from-blue-500/25 via-cyan-300/60 to-cyan-200 shadow-[0_-8px_20px_rgba(103,232,249,0.04)] transition"
                        >

                          <motion.span
                            className="absolute left-1/2 top-0 h-2 w-2 -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-100 opacity-0 shadow-[0_0_12px_rgba(103,232,249,0.6)] transition-opacity group-hover/bar:opacity-100"
                          />

                        </motion.div>

                      )
                    )}

                  </div>

                </div>


                {/* HEALTH METRICS */}

                <div className="mt-5 grid grid-cols-3 gap-3">


                  <motion.div
                    whileHover={{
                      y: -2,
                    }}
                    className="rounded-2xl border border-white/5 bg-white/[0.035] p-4"
                  >

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

                  </motion.div>


                  <motion.div
                    whileHover={{
                      y: -2,
                    }}
                    className="rounded-2xl border border-white/5 bg-white/[0.035] p-4"
                  >

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

                  </motion.div>


                  <motion.div
                    whileHover={{
                      y: -2,
                    }}
                    className="rounded-2xl border border-red-300/10 bg-red-300/[0.025] p-4"
                  >

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

                  </motion.div>

                </div>

              </div>

            </motion.div>

          </Link>


          {/* INVESTIGATION */}

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
            className="group relative overflow-hidden rounded-[2rem] border border-red-300/10 bg-red-300/[0.035] p-7 shadow-[0_18px_45px_rgba(0,0,0,0.09)] backdrop-blur-xl"
          >

            <motion.div
              className="pointer-events-none absolute -right-20 top-1/2 h-56 w-56 rounded-full bg-red-400/[0.035] blur-3xl"
              animate={{
                scale: [
                  1,
                  1.1,
                  1,
                ],
                opacity: [
                  0.45,
                  0.75,
                  0.45,
                ],
              }}
              transition={{
                duration: 5,
                repeat: Infinity,
                ease: "easeInOut",
              }}
            />


            <div className="relative">

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
                          x: 5,
                          scale: 1.01,
                        }}
                        className="group/item flex items-center justify-between rounded-2xl border border-white/5 bg-black/10 p-4 transition hover:border-red-300/10 hover:bg-white/[0.035]"
                      >

                        <div className="flex min-w-0 items-center gap-3">

                          <span
                            className={`h-2 w-2 shrink-0 rounded-full ${
                              level ===
                              "Critical"
                                ? "bg-red-300"
                                : "bg-amber-300"
                            }`}
                          />

                          <div>

                            <p className="text-sm font-medium">
                              {title}
                            </p>

                            <p className="mt-1 text-xs text-white/35">
                              Investigation signal detected
                            </p>

                          </div>

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


              <motion.div
                whileHover={{
                  scale: 1.01,
                }}
                className="mt-5"
              >

                <Link
                  href="/journeys"
                  className="flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-4 py-3 text-sm text-white/55 transition hover:border-red-300/15 hover:bg-white/10 hover:text-white"
                >

                  Open journey investigation

                  <ArrowUpRight className="h-4 w-4" />

                </Link>

              </motion.div>

            </div>

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
                    className="group relative h-full overflow-hidden rounded-3xl border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl"
                  >

                    <div className="pointer-events-none absolute -right-12 -top-12 h-24 w-24 rounded-full bg-cyan-300/[0.04] blur-2xl transition duration-500 group-hover:bg-cyan-300/[0.08]" />


                    <div className="relative">

                      <motion.div
                        whileHover={{
                          rotate: -5,
                          scale: 1.06,
                        }}
                        className="flex h-11 w-11 items-center justify-center rounded-2xl border border-white/5 bg-white/5"
                      >

                        <Icon className="h-5 w-5 text-cyan-300" />

                      </motion.div>


                      <h3 className="mt-6 font-semibold">
                        {module.title}
                      </h3>


                      <p className="mt-2 text-sm leading-6 text-white/40">
                        {module.description}
                      </p>


                      <div className="mt-6 flex items-center gap-2 text-xs text-white/35 transition group-hover:text-cyan-200">

                        Explore

                        <ArrowUpRight className="h-3.5 w-3.5 transition-transform group-hover:-translate-y-0.5 group-hover:translate-x-0.5" />

                      </div>

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