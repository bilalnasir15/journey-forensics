"use client";

import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  CheckCircle2,
  ChevronRight,
  CircleDollarSign,
  Clock3,
  CreditCard,
  Fingerprint,
  Gauge,
  Layers3,
  Loader2,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
  TriangleAlert,
  XCircle,
  Zap,
} from "lucide-react";

import { motion } from "motion/react";

import Link from "next/link";

import {
  type FormEvent,
  useMemo,
  useState,
} from "react";

import {
  getJourney,
  type Journey,
} from "@/lib/api";


// ============================================================
// CONSTANTS
// ============================================================

const EXAMPLE_BOOKING =
  "B007998";


const FORENSIC_POINTS = [
  {
    left: "8%",
    top: "18%",
    delay: 0,
    duration: 5.5,
  },
  {
    left: "18%",
    top: "72%",
    delay: 1.1,
    duration: 6.5,
  },
  {
    left: "31%",
    top: "28%",
    delay: 0.5,
    duration: 7,
  },
  {
    left: "46%",
    top: "81%",
    delay: 1.6,
    duration: 5.8,
  },
  {
    left: "62%",
    top: "16%",
    delay: 0.8,
    duration: 6.2,
  },
  {
    left: "74%",
    top: "67%",
    delay: 1.4,
    duration: 5.4,
  },
  {
    left: "87%",
    top: "23%",
    delay: 0.3,
    duration: 6.8,
  },
  {
    left: "94%",
    top: "76%",
    delay: 1.8,
    duration: 5.9,
  },
];


// ============================================================
// ANOMALY DEFINITIONS
// ============================================================

const anomalyDefinitions:
  Record<
    string,
    {
      title: string;
      description: string;
      severity: "HIGH" | "CRITICAL";
      icon: typeof AlertTriangle;
    }
  > = {

    MULTIPLE_PAYMENT_FAILURES: {
      title:
        "Multiple payment failures",

      description:
        "More than one payment attempt failed during the booking journey.",

      severity:
        "CRITICAL",

      icon:
        XCircle,
    },


    PAYMENT_RETRY_STORM: {
      title:
        "Payment retry storm",

      description:
        "Repeated payment attempts indicate elevated transaction friction.",

      severity:
        "HIGH",

      icon:
        RefreshCw,
    },


    PAYMENT_SUCCESS_BOOKING_UNRESOLVED: {
      title:
        "Payment succeeded but booking remains unresolved",

      description:
        "A successful payment signal exists while the booking outcome remains unresolved.",

      severity:
        "CRITICAL",

      icon:
        AlertTriangle,
    },
  };


// ============================================================
// ANOMALY PARSER
// ============================================================

function parseAnomalies(
  summary?: string | null
) {

  if (!summary) {
    return [];
  }


  return summary
    .split("|")
    .map(
      (
        item
      ) =>
        item.trim()
    )
    .filter(Boolean)
    .map(
      (
        code
      ) =>
        anomalyDefinitions[
          code
        ] ?? {
          title: code
            .replaceAll(
              "_",
              " "
            )
            .toLowerCase()
            .replace(
              /\b\w/g,
              (character) =>
                character.toUpperCase()
            ),

          description:
            "An analytical signal was detected for this journey.",

          severity:
            "HIGH",

          icon:
            TriangleAlert,
        }
    );
}


// ============================================================
// HELPERS
// ============================================================

function riskClass(
  risk: string | null | undefined
) {

  switch (
    risk?.toUpperCase()
  ) {

    case "CRITICAL":
      return "border-red-300/25 bg-red-300/10 text-red-200";

    case "HIGH":
      return "border-orange-300/25 bg-orange-300/10 text-orange-200";

    case "MEDIUM":
      return "border-amber-300/25 bg-amber-300/10 text-amber-200";

    case "LOW":
      return "border-emerald-300/25 bg-emerald-300/10 text-emerald-200";

    default:
      return "border-white/10 bg-white/5 text-white/50";
  }
}


function formatCurrency(
  value: number | null | undefined
) {

  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }


  return value.toLocaleString(
    undefined,
    {
      minimumFractionDigits: 2,
      maximumFractionDigits: 2,
    }
  );
}


function formatNumber(
  value: number | null | undefined,
  digits = 2
) {

  if (
    value === null ||
    value === undefined
  ) {
    return "—";
  }


  return value.toFixed(
    digits
  );
}


// ============================================================
// TIMELINE ITEM
// ============================================================

function TimelineItem({
  title,
  count,
  description,
  icon: Icon,
  tone,
  index,
  totalItems,
}: {
  title: string;
  count: number;
  description: string;
  icon: typeof Activity;
  tone:
    | "neutral"
    | "danger"
    | "success"
    | "warning";
  index: number;
  totalItems: number;
}) {

  const toneClass = {

    neutral:
      "border-white/10 bg-white/[0.035] text-cyan-300",

    danger:
      "border-red-300/15 bg-red-300/[0.035] text-red-300",

    success:
      "border-emerald-300/15 bg-emerald-300/[0.035] text-emerald-300",

    warning:
      "border-amber-300/15 bg-amber-300/[0.035] text-amber-300",

  }[tone];


  return (

    <motion.div
      initial={{
        opacity: 0,
        x: -16,
      }}
      animate={{
        opacity: 1,
        x: 0,
      }}
      transition={{
        delay:
          index * 0.05,
        duration: 0.4,
      }}
      className="group relative flex gap-4"
    >

      {index <
        totalItems - 1 && (
        <div className="absolute left-[19px] top-10 h-[calc(100%+1rem)] w-px bg-gradient-to-b from-white/15 via-white/8 to-transparent" />
      )}


      <motion.div
        whileHover={{
          scale: 1.08,
          boxShadow:
            "0 0 24px rgba(103,232,249,0.08)",
        }}
        className={`relative z-10 flex h-10 w-10 shrink-0 items-center justify-center rounded-2xl border transition ${toneClass}`}
      >

        <Icon className="h-4 w-4" />

      </motion.div>


      <motion.div
        whileHover={{
          x: 3,
        }}
        className="min-w-0 flex-1 rounded-2xl border border-white/5 bg-black/10 px-4 py-3 transition hover:border-cyan-300/10 hover:bg-white/[0.025]"
      >

        <div className="flex items-center justify-between gap-3">

          <div>

            <p className="text-sm font-medium">
              {title}
            </p>

            <p className="mt-1 text-xs leading-5 text-white/30">
              {description}
            </p>

          </div>


          <span className="rounded-full border border-white/5 bg-white/5 px-3 py-1 text-xs text-white/50">
            {count}
          </span>

        </div>

      </motion.div>

    </motion.div>
  );
}


// ============================================================
// METRIC MINI
// ============================================================

function MetricMini({
  label,
  value,
}: {
  label: string;
  value: string;
}) {

  return (

    <motion.div
      whileHover={{
        y: -2,
      }}
      className="rounded-2xl border border-white/10 bg-black/10 px-5 py-4 transition hover:border-cyan-300/10"
    >

      <p className="text-[10px] uppercase tracking-[0.14em] text-white/25">
        {label}
      </p>


      <p className="mt-1 text-sm font-semibold">
        {value}
      </p>

    </motion.div>
  );
}


// ============================================================
// FORENSIC ROW
// ============================================================

function ForensicRow({
  label,
  value,
  positive = false,
  negative = false,
  warning = false,
}: {
  label: string;
  value: string;
  positive?: boolean;
  negative?: boolean;
  warning?: boolean;
}) {

  let valueClass =
    "text-white/75";


  if (positive) {
    valueClass =
      "text-emerald-200";
  }


  if (negative) {
    valueClass =
      "text-red-200";
  }


  if (warning) {
    valueClass =
      "text-amber-200";
  }


  return (

    <div className="flex items-center justify-between rounded-2xl bg-black/10 px-4 py-3">

      <span className="text-xs text-white/35">
        {label}
      </span>


      <span
        className={`text-sm font-semibold ${valueClass}`}
      >
        {value}
      </span>

    </div>
  );
}


// ============================================================
// SIGNAL BAR
// ============================================================

function SignalBar({
  label,
  value,
  max,
  tone,
}: {
  label: string;
  value: number;
  max: number;
  tone:
    | "cyan"
    | "red"
    | "amber";
}) {

  const percentage =
    max > 0
      ? Math.min(
          100,
          (value / max) *
            100
        )
      : 0;


  const barClass = {

    cyan:
      "from-cyan-300 to-blue-400",

    red:
      "from-red-300 to-orange-300",

    amber:
      "from-amber-300 to-orange-300",

  }[tone];


  return (

    <div>

      <div className="mb-2 flex items-center justify-between text-xs">

        <span className="text-white/35">
          {label}
        </span>

        <span className="text-white/65">
          {value}
        </span>

      </div>


      <div className="h-2 overflow-hidden rounded-full bg-white/5">

        <motion.div
          initial={{
            width: 0,
          }}
          animate={{
            width:
              `${percentage}%`,
          }}
          transition={{
            duration:
              0.9,
            ease:
              "easeOut",
          }}
          className={`h-full rounded-full bg-gradient-to-r ${barClass}`}
        />

      </div>

    </div>
  );
}


// ============================================================
// CONCLUSION METRIC
// ============================================================

function ConclusionMetric({
  label,
  value,
  icon: Icon,
}: {
  label: string;
  value: string;
  icon: typeof Activity;
}) {

  return (

    <motion.div
      whileHover={{
        y: -2,
      }}
      className="rounded-2xl border border-white/5 bg-black/10 p-4 transition hover:border-cyan-300/10"
    >

      <div className="flex items-center gap-2 text-xs text-white/35">

        <Icon className="h-3.5 w-3.5 text-cyan-300" />

        {label}

      </div>


      <p className="mt-2 text-sm font-semibold">
        {value}
      </p>

    </motion.div>
  );
}


// ============================================================
// PAGE
// ============================================================

export default function JourneysPage() {

  const [
    bookingId,
    setBookingId,
  ] = useState(
    EXAMPLE_BOOKING
  );


  const [
    journey,
    setJourney,
  ] = useState<Journey | null>(
    null
  );


  const [
    loading,
    setLoading,
  ] = useState(false);


  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );


  const [
    searched,
    setSearched,
  ] = useState(false);


  // ==========================================================
  // LOOKUP
  // ==========================================================

  async function investigateJourney(
    id: string
  ) {

    const normalized =
      id.trim();


    if (!normalized) {

      setJourney(null);

      setSearched(true);

      setError(
        "Please enter a booking ID."
      );

      return;
    }


    try {

      setLoading(true);

      setSearched(true);

      setError(null);


      const response =
        await getJourney(
          normalized
        );


      setJourney(
        response
      );

    } catch (err) {

      setJourney(null);

      setError(
        err instanceof Error
          ? err.message
          : "Journey could not be loaded."
      );

    } finally {

      setLoading(false);

    }
  }


  async function handleSearch(
    event: FormEvent
  ) {

    event.preventDefault();

    await investigateJourney(
      bookingId
    );
  }


  async function loadExample() {

    setBookingId(
      EXAMPLE_BOOKING
    );

    await investigateJourney(
      EXAMPLE_BOOKING
    );
  }


  // ==========================================================
  // DERIVED
  // ==========================================================

  const anomalies =
    useMemo(
      () =>
        parseAnomalies(
          journey?.anomaly_summary
        ),
      [
        journey?.anomaly_summary,
      ]
    );


  const criticalFindings =
    useMemo(
      () =>
        anomalies.filter(
          (item) =>
            item.severity ===
            "CRITICAL"
        ),
      [
        anomalies,
      ]
    );


  const paymentAttemptMax =
    Math.max(
      journey?.payment_attempts ??
        0,
      1
    );


  const isCritical =
    journey?.risk_level?.toUpperCase() ===
    "CRITICAL";


  const paymentSuccessPercent =
    journey?.payment_success_rate !==
      null &&
    journey?.payment_success_rate !==
      undefined
      ? journey.payment_success_rate *
        100
      : null;


  return (

    <main className="relative min-h-screen overflow-hidden bg-[#07111f] text-white">


      {/* ======================================================
          FORENSIC BACKGROUND
          ====================================================== */}

      <div
        className="pointer-events-none fixed inset-0 overflow-hidden"
        aria-hidden="true"
      >

        {/* Atmosphere */}

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_10%,rgba(34,211,238,0.06),transparent_28%),radial-gradient(circle_at_90%_30%,rgba(139,92,246,0.07),transparent_32%)]" />


        {/* Grid */}

        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(103,232,249,.25) 1px, transparent 1px), linear-gradient(90deg, rgba(103,232,249,.25) 1px, transparent 1px)",
            backgroundSize:
              "72px 72px",
            maskImage:
              "radial-gradient(circle at center, black 15%, transparent 85%)",
            WebkitMaskImage:
              "radial-gradient(circle at center, black 15%, transparent 85%)",
          }}
        />


        {/* Cyan field */}

        <motion.div
          className="absolute -left-48 top-20 h-[34rem] w-[34rem] rounded-full bg-cyan-400/[0.055] blur-3xl"
          animate={{
            x: [
              0,
              65,
              0,
            ],

            y: [
              0,
              40,
              0,
            ],

            scale: [
              1,
              1.1,
              1,
            ],
          }}
          transition={{
            duration: 14,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />


        {/* Violet field */}

        <motion.div
          className="absolute right-[-180px] top-[35%] h-[38rem] w-[38rem] rounded-full bg-violet-500/[0.06] blur-3xl"
          animate={{
            x: [
              0,
              -60,
              0,
            ],

            y: [
              0,
              45,
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


        {/* Radar rings */}

        <div className="absolute left-[5%] top-[32%] hidden h-72 w-72 md:block">

          <motion.div
            className="absolute inset-0 rounded-full border border-cyan-300/[0.07]"
            animate={{
              scale: [
                0.8,
                1.06,
                0.8,
              ],
              opacity: [
                0.15,
                0.48,
                0.15,
              ],
            }}
            transition={{
              duration: 8,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />


          <motion.div
            className="absolute inset-9 rounded-full border border-cyan-300/[0.06]"
            animate={{
              rotate: 360,
            }}
            transition={{
              duration: 28,
              repeat: Infinity,
              ease: "linear",
            }}
          />


          <div className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-300/40 shadow-[0_0_14px_rgba(103,232,249,0.4)]" />

        </div>


        <div className="absolute right-[5%] top-[58%] hidden h-80 w-80 lg:block">

          <motion.div
            className="absolute inset-0 rounded-full border border-violet-300/[0.06]"
            animate={{
              scale: [
                0.82,
                1.05,
                0.82,
              ],
              opacity: [
                0.15,
                0.42,
                0.15,
              ],
            }}
            transition={{
              duration: 10,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />


          <motion.div
            className="absolute inset-10 rounded-full border border-violet-300/[0.05]"
            animate={{
              rotate: -360,
            }}
            transition={{
              duration: 34,
              repeat: Infinity,
              ease: "linear",
            }}
          />

        </div>


        {/* Scan lines */}

        <motion.div
          className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-cyan-300/15 to-transparent"
          animate={{
            top: [
              "6%",
              "94%",
              "6%",
            ],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear",
          }}
        />


        {FORENSIC_POINTS.map(
          (
            point,
            index
          ) => (

            <motion.span
              key={index}
              className="absolute h-1.5 w-1.5 rounded-full bg-cyan-200/25"
              style={{
                left:
                  point.left,
                top:
                  point.top,
              }}
              animate={{
                y: [
                  0,
                  -12,
                  0,
                ],

                opacity: [
                  0.08,
                  0.45,
                  0.08,
                ],

                scale: [
                  0.8,
                  1.12,
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
                ease:
                  "easeInOut",
              }}
            />

          )
        )}


        {/* Vignette */}

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_center,transparent_40%,rgba(3,10,20,0.2)_100%)]" />

      </div>


      {/* ======================================================
          CONTENT
          ====================================================== */}

      <section className="relative z-10 mx-auto max-w-7xl px-6 py-10">


        {/* ====================================================
            HERO
            ==================================================== */}

        <motion.div
          initial={{
            opacity: 0,
            y: 18,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
        >

          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-white/40 transition hover:text-white"
          >

            <ArrowLeft className="h-4 w-4" />

            Back to overview

          </Link>


          <div className="mt-8 flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">

            <div>

              <div className="flex items-center gap-2 text-sm text-cyan-300/75">

                <Sparkles className="h-4 w-4" />

                Forensic journey intelligence

              </div>


              <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">

                Follow the evidence.

                <span className="block bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400 bg-clip-text text-transparent">
                  Find the friction.
                </span>

              </h1>


              <p className="mt-5 max-w-3xl text-base leading-7 text-white/45">

                Trace a booking through behavioural events,
                payment activity, friction signals and
                forensic findings.

              </p>

            </div>


            <motion.div
              whileHover={{
                y: -2,
              }}
              className="flex items-center gap-2 rounded-full border border-emerald-300/10 bg-emerald-300/5 px-4 py-2 text-xs text-emerald-200/80"
            >

              <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />

              Live journey source

            </motion.div>

          </div>

        </motion.div>


        {/* ====================================================
            SEARCH
            ==================================================== */}

        <motion.form
          initial={{
            opacity: 0,
            y: 18,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            delay: 0.08,
          }}
          onSubmit={
            handleSearch
          }
          className="relative mt-9 overflow-hidden rounded-[2rem] border border-white/10 bg-white/[0.035] p-5 shadow-[0_18px_45px_rgba(0,0,0,0.08)] backdrop-blur-xl"
        >

          <div className="pointer-events-none absolute right-0 top-0 h-32 w-32 rounded-full bg-cyan-300/[0.035] blur-3xl" />


          <div className="relative flex flex-col gap-4 lg:flex-row lg:items-end">

            <div className="flex-1">

              <label
                htmlFor="booking-id"
                className="mb-2 block text-xs text-white/35"
              >
                Investigate booking
              </label>


              <div className="relative">

                <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-white/25" />


                <input
                  id="booking-id"
                  value={
                    bookingId
                  }
                  onChange={(
                    event
                  ) =>
                    setBookingId(
                      event.target.value
                    )
                  }
                  placeholder="Enter booking ID, e.g. B007998"
                  className="w-full rounded-2xl border border-white/10 bg-[#07111f]/65 py-4 pl-11 pr-4 text-sm text-white outline-none placeholder:text-white/20 transition focus:border-cyan-300/30 focus:ring-4 focus:ring-cyan-300/[0.04]"
                />

              </div>


              <button
                type="button"
                onClick={
                  loadExample
                }
                className="mt-2 text-[11px] text-cyan-300/60 transition hover:text-cyan-200"
              >

                Load validated example:{" "}

                {EXAMPLE_BOOKING}

              </button>

            </div>


            <motion.button
              type="submit"
              disabled={
                loading
              }
              whileHover={{
                scale:
                  loading
                    ? 1
                    : 1.02,
                boxShadow:
                  loading
                    ? undefined
                    : "0 0 30px rgba(103,232,249,0.12)",
              }}
              whileTap={{
                scale:
                  loading
                    ? 1
                    : 0.98,
              }}
              className="flex min-h-[54px] items-center justify-center gap-2 rounded-2xl bg-cyan-300 px-7 font-medium text-[#07111f] transition disabled:opacity-60"
            >

              {loading ? (
                <>
                  <Loader2 className="h-4 w-4 animate-spin" />

                  Investigating...
                </>
              ) : (
                <>
                  Investigate journey

                  <ArrowRight className="h-4 w-4" />
                </>
              )}

            </motion.button>

          </div>

        </motion.form>


        {/* ====================================================
            ERROR
            ==================================================== */}

        {searched &&
          error && (

            <motion.div
              initial={{
                opacity: 0,
                y: 10,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              className="mt-5 flex items-start gap-3 rounded-2xl border border-red-300/15 bg-red-300/[0.04] p-5"
            >

              <XCircle className="h-5 w-5 text-red-300" />

              <div>

                <p className="text-sm font-medium text-red-200">
                  Journey unavailable
                </p>

                <p className="mt-1 text-sm text-white/40">
                  {error}
                </p>

              </div>

            </motion.div>

          )}


        {/* ====================================================
            EMPTY
            ==================================================== */}

        {!journey &&
          !loading &&
          !error && (

            <motion.div
              initial={{
                opacity: 0,
                y: 15,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              className="relative mt-8 overflow-hidden rounded-[2rem] border border-white/10 bg-white/[0.035] p-14 text-center backdrop-blur-xl"
            >

              <div className="pointer-events-none absolute left-1/2 top-0 h-40 w-64 -translate-x-1/2 rounded-full bg-cyan-300/[0.035] blur-3xl" />


              <div className="relative">

                <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl border border-cyan-300/15 bg-cyan-300/5">

                  <Fingerprint className="h-7 w-7 text-cyan-300" />

                </div>


                <h2 className="mt-5 text-2xl font-semibold">
                  Start a forensic investigation
                </h2>


                <p className="mx-auto mt-3 max-w-xl text-sm leading-6 text-white/35">

                  Enter a booking ID to uncover payment
                  friction, retries, failures, journey
                  behavior and anomaly evidence.

                </p>

              </div>

            </motion.div>

          )}


        {/* ====================================================
            RESULT
            ==================================================== */}

        {journey && (

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
              duration: 0.55,
            }}
            className="mt-8"
          >

            {/* =================================================
                CASE HEADER
                ================================================= */}

            <motion.div
              whileHover={{
                borderColor:
                  "rgba(103,232,249,0.14)",
              }}
              className={`relative overflow-hidden rounded-[2rem] border p-6 backdrop-blur-xl ${
                isCritical
                  ? "border-red-300/15 bg-red-300/[0.025]"
                  : "border-white/10 bg-white/[0.04]"
              }`}
            >

              <div className="pointer-events-none absolute -right-20 -top-20 h-40 w-40 rounded-full bg-cyan-300/[0.035] blur-3xl" />


              <div className="relative flex flex-col gap-6 xl:flex-row xl:items-center xl:justify-between">

                <div className="flex items-center gap-4">

                  <motion.div
                    animate={{
                      boxShadow: [
                        "0 0 0 rgba(103,232,249,0)",
                        "0 0 32px rgba(103,232,249,0.09)",
                        "0 0 0 rgba(103,232,249,0)",
                      ],
                    }}
                    transition={{
                      duration:
                        3.2,
                      repeat:
                        Infinity,
                    }}
                    className="flex h-16 w-16 shrink-0 items-center justify-center rounded-3xl border border-cyan-300/20 bg-cyan-300/10"
                  >

                    <Fingerprint className="h-7 w-7 text-cyan-300" />

                  </motion.div>


                  <div>

                    <div className="flex flex-wrap items-center gap-3">

                      <h2 className="text-2xl font-semibold">
                        {journey.booking_id}
                      </h2>


                      <span
                        className={`rounded-full border px-3 py-1 text-xs font-medium ${riskClass(
                          journey.risk_level
                        )}`}
                      >

                        {journey.risk_level ??
                          "UNASSESSED"}

                      </span>

                    </div>


                    <p className="mt-2 text-sm text-white/35">

                      Customer{" "}

                      <span className="text-white/70">
                        {journey.customer_id}
                      </span>

                      {" · "}

                      Trip{" "}

                      <span className="text-white/70">
                        {journey.trip_id ??
                          "Unknown"}
                      </span>

                    </p>

                  </div>

                </div>


                <div className="grid gap-3 sm:grid-cols-2">

                  <MetricMini
                    label="Booking status"
                    value={
                      journey.booking_status ??
                      "Unknown"
                    }
                  />


                  <MetricMini
                    label="Booking amount"
                    value={formatCurrency(
                      journey.booking_amount
                    )}
                  />

                </div>

              </div>

            </motion.div>


            {/* =================================================
                KEY METRICS
                ================================================= */}

            <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-5">

              {[
                {
                  label:
                    "Journey duration",
                  value:
                    journey.journey_duration_minutes !==
                      null &&
                    journey.journey_duration_minutes !==
                      undefined
                      ? `${formatNumber(
                          journey.journey_duration_minutes
                        )}m`
                      : "—",
                  icon:
                    Clock3,
                },

                {
                  label:
                    "Payment duration",
                  value:
                    journey.payment_duration_minutes !==
                      null &&
                    journey.payment_duration_minutes !==
                      undefined
                      ? `${formatNumber(
                          journey.payment_duration_minutes
                        )}m`
                      : "—",
                  icon:
                    CreditCard,
                },

                {
                  label:
                    "Friction score",
                  value:
                    journey.friction_score !==
                      null &&
                    journey.friction_score !==
                      undefined
                      ? formatNumber(
                          journey.friction_score
                        )
                      : "—",
                  icon:
                    Gauge,
                },

                {
                  label:
                    "Payment success",
                  value:
                    paymentSuccessPercent !==
                      null
                      ? `${paymentSuccessPercent.toFixed(
                          1
                        )}%`
                      : "—",
                  icon:
                    CheckCircle2,
                },

                {
                  label:
                    "Total events",
                  value:
                    journey.total_events.toLocaleString(),
                  icon:
                    Activity,
                },
              ].map(
                (
                  card,
                  index
                ) => {

                  const Icon =
                    card.icon;

                  return (

                    <motion.div
                      key={
                        card.label
                      }
                      initial={{
                        opacity: 0,
                        y: 15,
                      }}
                      animate={{
                        opacity: 1,
                        y: 0,
                      }}
                      transition={{
                        delay:
                          index *
                          0.05,
                      }}
                      whileHover={{
                        y: -5,
                      }}
                      className="group rounded-3xl border border-white/10 bg-white/[0.04] p-5 backdrop-blur-xl"
                    >

                      <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-white/5 bg-white/5 transition group-hover:border-cyan-300/10 group-hover:bg-cyan-300/[0.05]">

                        <Icon className="h-5 w-5 text-cyan-300" />

                      </div>


                      <p className="mt-5 text-xs text-white/30">
                        {card.label}
                      </p>


                      <p className="mt-1 text-2xl font-semibold tracking-tight">
                        {card.value}
                      </p>

                    </motion.div>

                  );
                }
              )}

            </div>


            {/* =================================================
                FORENSIC FINDINGS
                ================================================= */}

            {anomalies.length >
              0 && (

              <motion.section
                initial={{
                  opacity: 0,
                  y: 18,
                }}
                animate={{
                  opacity: 1,
                  y: 0,
                }}
                transition={{
                  delay: 0.22,
                }}
                className={`mt-5 rounded-[2rem] border p-6 backdrop-blur-xl ${
                  isCritical
                    ? "border-red-300/15 bg-red-300/[0.025]"
                    : "border-white/10 bg-white/[0.04]"
                }`}
              >

                <div className="flex flex-col gap-4 sm:flex-row sm:items-start sm:justify-between">

                  <div>

                    <div className="flex items-center gap-2 text-sm text-red-200/70">

                      <TriangleAlert className="h-4 w-4" />

                      Detected forensic findings

                    </div>


                    <h3 className="mt-2 text-2xl font-semibold">
                      {criticalFindings.length} critical signals
                    </h3>


                    <p className="mt-1 text-xs text-white/30">
                      Analytical findings reconstructed from the validated journey evidence.
                    </p>

                  </div>


                  <div className="rounded-full border border-red-300/15 bg-red-300/5 px-3 py-1 text-[10px] uppercase tracking-wider text-red-200/70">

                    Attention required

                  </div>

                </div>


                <div className="mt-6 grid gap-3 lg:grid-cols-3">

                  {anomalies.map(
                    (
                      finding,
                      index
                    ) => {

                      const Icon =
                        finding.icon;


                      return (

                        <motion.div
                          key={
                            `${finding.title}-${index}`
                          }
                          initial={{
                            opacity: 0,
                            y: 12,
                          }}
                          animate={{
                            opacity: 1,
                            y: 0,
                          }}
                          transition={{
                            delay:
                              0.28 +
                              index *
                                0.08,
                          }}
                          whileHover={{
                            y: -4,
                          }}
                          className="group rounded-3xl border border-white/10 bg-black/10 p-5 transition hover:border-red-300/10"
                        >

                          <div className="flex items-start justify-between gap-3">

                            <motion.div
                              whileHover={{
                                rotate:
                                  5,
                              }}
                              className="flex h-10 w-10 items-center justify-center rounded-2xl bg-red-300/10"
                            >

                              <Icon className="h-5 w-5 text-red-300" />

                            </motion.div>


                            <span
                              className={`rounded-full border px-2.5 py-1 text-[9px] font-medium uppercase ${
                                finding.severity ===
                                "CRITICAL"
                                  ? "border-red-300/15 bg-red-300/5 text-red-200"
                                  : "border-amber-300/15 bg-amber-300/5 text-amber-200"
                              }`}
                            >

                              {finding.severity}

                            </span>

                          </div>


                          <h4 className="mt-5 text-sm font-semibold">
                            {finding.title}
                          </h4>


                          <p className="mt-2 text-xs leading-6 text-white/35">
                            {finding.description}
                          </p>

                        </motion.div>

                      );
                    }
                  )}

                </div>

              </motion.section>

            )}


            {/* =================================================
                MAIN FORENSIC
                ================================================= */}

            <div className="mt-5 grid gap-5 xl:grid-cols-[1.2fr_0.8fr]">


              {/* =================================================
                  TIMELINE
                  ================================================= */}

              <section className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl">

                <div className="flex items-start justify-between">

                  <div>

                    <div className="flex items-center gap-2 text-sm text-white/45">

                      <Zap className="h-4 w-4 text-cyan-300" />

                      Journey evidence

                    </div>


                    <h3 className="mt-2 text-xl font-semibold">
                      Event progression
                    </h3>

                  </div>


                  <div className="rounded-full border border-cyan-300/10 bg-cyan-300/5 px-3 py-1 text-xs text-cyan-200/70">

                    {journey.total_events} events

                  </div>

                </div>


                <div className="mt-7 space-y-4">

                  <TimelineItem
                    index={0}
                    totalItems={8}
                    title="Search"
                    count={
                      journey.search_events
                    }
                    description="Customer discovered or searched for a trip."
                    icon={
                      Search
                    }
                    tone="neutral"
                  />


                  <TimelineItem
                    index={1}
                    totalItems={8}
                    title="View trip"
                    count={
                      journey.view_trip_events
                    }
                    description="Trip details were inspected."
                    icon={
                      Layers3
                    }
                    tone="neutral"
                  />


                  <TimelineItem
                    index={2}
                    totalItems={8}
                    title="Booking started"
                    count={
                      journey.booking_started_events
                    }
                    description="Customer entered the booking flow."
                    icon={
                      ArrowRight
                    }
                    tone="neutral"
                  />


                  <TimelineItem
                    index={3}
                    totalItems={8}
                    title="Booking created"
                    count={
                      journey.booking_created_events
                    }
                    description="A booking record was created."
                    icon={
                      CheckCircle2
                    }
                    tone="neutral"
                  />


                  <TimelineItem
                    index={4}
                    totalItems={8}
                    title="Payment started"
                    count={
                      journey.payment_started_events
                    }
                    description="Payment processing was initiated."
                    icon={
                      CreditCard
                    }
                    tone="warning"
                  />


                  <TimelineItem
                    index={5}
                    totalItems={8}
                    title="Payment failed"
                    count={
                      journey.payment_failed_events
                    }
                    description="Payment failure signals were detected."
                    icon={
                      XCircle
                    }
                    tone={
                      journey.payment_failed_events >
                      0
                        ? "danger"
                        : "neutral"
                    }
                  />


                  <TimelineItem
                    index={6}
                    totalItems={8}
                    title="Payment retry"
                    count={
                      journey.payment_retry_events
                    }
                    description="Payment was retried by the customer or system."
                    icon={
                      RefreshCw
                    }
                    tone={
                      journey.payment_retry_events >
                      0
                        ? "warning"
                        : "neutral"
                    }
                  />


                  <TimelineItem
                    index={7}
                    totalItems={8}
                    title="Payment completed"
                    count={
                      journey.payment_completed_events
                    }
                    description="Payment completed successfully."
                    icon={
                      CheckCircle2
                    }
                    tone={
                      journey.payment_completed_events >
                      0
                        ? "success"
                        : "neutral"
                    }
                  />

                </div>

              </section>


              {/* =================================================
                  PAYMENT + RISK
                  ================================================= */}

              <div className="space-y-5">


                <section className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl">

                  <div className="flex items-center gap-2 text-sm text-white/45">

                    <CreditCard className="h-4 w-4 text-cyan-300" />

                    Payment forensics

                  </div>


                  <h3 className="mt-2 text-xl font-semibold">
                    Payment behavior
                  </h3>


                  <div className="mt-6 space-y-3">

                    <ForensicRow
                      label="Payment attempts"
                      value={
                        journey.payment_attempts.toString()
                      }
                    />


                    <ForensicRow
                      label="Successful payments"
                      value={
                        journey.successful_payments.toString()
                      }
                      positive
                    />


                    <ForensicRow
                      label="Failed payments"
                      value={
                        journey.failed_payments.toString()
                      }
                      negative={
                        journey.failed_payments >
                        0
                      }
                    />


                    <ForensicRow
                      label="Payment retries"
                      value={
                        journey.retry_count.toString()
                      }
                      warning={
                        journey.retry_count >
                        0
                      }
                    />

                  </div>


                  <div className="mt-6 space-y-5">

                    <SignalBar
                      label="Payment attempts"
                      value={
                        journey.payment_attempts
                      }
                      max={
                        paymentAttemptMax
                      }
                      tone="cyan"
                    />


                    <SignalBar
                      label="Failed attempts"
                      value={
                        journey.failed_payments
                      }
                      max={
                        paymentAttemptMax
                      }
                      tone="red"
                    />


                    <SignalBar
                      label="Retries"
                      value={
                        journey.retry_count
                      }
                      max={
                        paymentAttemptMax
                      }
                      tone="amber"
                    />

                  </div>

                </section>


                <section
                  className={`rounded-[2rem] border p-6 backdrop-blur-xl ${
                    isCritical
                      ? "border-red-300/15 bg-red-300/[0.035]"
                      : "border-white/10 bg-white/[0.04]"
                  }`}
                >

                  <div className="flex items-center gap-2 text-sm text-white/45">

                    <ShieldAlert className="h-4 w-4 text-red-300" />

                    Risk assessment

                  </div>


                  <div className="mt-6 flex items-center justify-between">

                    <span className="text-xs text-white/35">
                      Risk level
                    </span>


                    <span
                      className={`rounded-full border px-3 py-1 text-xs font-medium ${riskClass(
                        journey.risk_level
                      )}`}
                    >

                      {journey.risk_level ??
                        "UNASSESSED"}

                    </span>

                  </div>


                  <div className="mt-6">

                    <div className="flex items-end justify-between">

                      <div>

                        <p className="text-xs text-white/30">
                          Friction score
                        </p>


                        <p className="mt-1 text-4xl font-semibold">
                          {formatNumber(
                            journey.friction_score
                          )}
                        </p>

                      </div>


                      <Gauge className="h-6 w-6 text-cyan-300/60" />

                    </div>


                    <div className="mt-4 h-3 overflow-hidden rounded-full bg-white/5">

                      <motion.div
                        initial={{
                          width: 0,
                        }}
                        animate={{
                          width: `${Math.min(
                            100,
                            Math.max(
                              0,
                              journey.friction_score ??
                                0
                            )
                          )}%`,
                        }}
                        transition={{
                          duration:
                            1.1,
                          ease:
                            "easeOut",
                        }}
                        className="h-full rounded-full bg-gradient-to-r from-cyan-300 via-amber-300 to-red-300"
                      />

                    </div>

                  </div>

                </section>

              </div>

            </div>


            {/* =================================================
                CONCLUSION
                ================================================= */}

            <motion.section
              initial={{
                opacity: 0,
                y: 18,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              transition={{
                delay: 0.35,
              }}
              className={`mt-5 rounded-[2rem] border p-6 backdrop-blur-xl ${
                isCritical
                  ? "border-red-300/15 bg-red-300/[0.035]"
                  : "border-white/10 bg-white/[0.04]"
              }`}
            >

              <div className="flex items-start gap-4">

                <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-red-300/10">

                  <ShieldAlert className="h-6 w-6 text-red-300" />

                </div>


                <div className="min-w-0 flex-1">

                  <div className="flex flex-wrap items-center gap-3">

                    <h3 className="text-xl font-semibold">
                      Forensic conclusion
                    </h3>


                    <span
                      className={`rounded-full border px-3 py-1 text-[10px] font-medium uppercase ${riskClass(
                        journey.risk_level
                      )}`}
                    >

                      {journey.risk_level ??
                        "UNASSESSED"}

                    </span>

                  </div>


                  <p className="mt-3 max-w-4xl text-sm leading-7 text-white/50">

                    {journey.anomaly_summary
                      ? "The journey contains one or more analytical signals that require investigation. The evidence above shows the payment and behavioural sequence supporting the current risk assessment."
                      : "No anomaly signal was returned for this journey."}

                  </p>


                  <div className="mt-5 grid gap-3 sm:grid-cols-2 xl:grid-cols-4">

                    <ConclusionMetric
                      label="Booking value"
                      value={formatCurrency(
                        journey.booking_amount
                      )}
                      icon={
                        CircleDollarSign
                      }
                    />


                    <ConclusionMetric
                      label="Payment outcome"
                      value={`${journey.successful_payments} successful`}
                      icon={
                        CheckCircle2
                      }
                    />


                    <ConclusionMetric
                      label="Event volume"
                      value={
                        journey.total_events.toLocaleString()
                      }
                      icon={
                        Activity
                      }
                    />


                    <ConclusionMetric
                      label="Journey pressure"
                      value={formatNumber(
                        journey.friction_score
                      )}
                      icon={
                        Gauge
                      }
                    />

                  </div>

                </div>

              </div>

            </motion.section>


            {/* =================================================
                NAVIGATION
                ================================================= */}

            <div className="mt-6 flex flex-wrap gap-3 pb-8">

              <Link
                href="/customers"
                className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm text-white/55 transition hover:border-cyan-300/10 hover:bg-white/10 hover:text-white"
              >

                <ArrowLeft className="h-4 w-4" />

                Customer intelligence

              </Link>


              <Link
                href="/kpis"
                className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm text-white/55 transition hover:border-cyan-300/10 hover:bg-white/10 hover:text-white"
              >

                KPI intelligence

                <ChevronRight className="h-4 w-4" />

              </Link>

            </div>

          </motion.div>

        )}

      </section>


      {/* ======================================================
          FOOTER
          ====================================================== */}

      <footer className="relative z-10 border-t border-white/10 px-6 py-6">

        <div className="mx-auto flex max-w-7xl justify-between text-xs text-white/25">

          <span>
            Journey Forensics
          </span>

          <span>
            Forensic intelligence engine
          </span>

        </div>

      </footer>

    </main>
  );
}