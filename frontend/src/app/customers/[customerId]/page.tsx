"use client";

import {
  Activity,
  ArrowLeft,
  BarChart3,
  CalendarDays,
  CheckCircle2,
  CircleDollarSign,
  Clock3,
  Fingerprint,
  Gauge,
  Layers3,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  UserRound,
  XCircle,
  Zap,
} from "lucide-react";

import {
  motion,
} from "motion/react";

import Link from "next/link";

import {
  useEffect,
  useState,
} from "react";

import {
  useParams,
} from "next/navigation";

import {
  getProfile,
  type Profile,
} from "@/lib/api";


// ============================================================
// HELPERS
// ============================================================

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


function segmentClass(
  segment: string
) {
  switch (
    segment.toUpperCase()
  ) {
    case "VIP":
      return "border-violet-300/20 bg-violet-300/10 text-violet-200";

    case "LOYAL":
      return "border-emerald-300/20 bg-emerald-300/10 text-emerald-200";

    case "AT_RISK":
      return "border-red-300/20 bg-red-300/10 text-red-200";

    case "DORMANT":
      return "border-amber-300/20 bg-amber-300/10 text-amber-200";

    case "NEW":
      return "border-cyan-300/20 bg-cyan-300/10 text-cyan-200";

    default:
      return "border-white/10 bg-white/5 text-white/55";
  }
}


function formatSegment(
  segment: string
) {
  return segment
    .replaceAll("_", " ")
    .toLowerCase()
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase()
    );
}


function segmentationMethodLabel(
  method: string
) {
  const normalized =
    method.toUpperCase();

  if (
    normalized.includes(
      "RULE_BASED_PRIMARY"
    )
  ) {
    return "Rule-based primary segmentation";
  }

  if (
    normalized.includes(
      "COHORT"
    )
  ) {
    return "Cohort-aware segmentation";
  }

  if (
    normalized.includes(
      "EXPLORATORY_CLUSTER"
    )
  ) {
    return "Exploratory behavioral clustering";
  }

  return "Validated analytical segmentation";
}


function complaintStatusClass(
  status: string
) {
  if (
    status ===
    "NOT_SUPPORTED"
  ) {
    return "border-red-300/15 bg-red-300/5 text-red-200/70";
  }

  return "border-emerald-300/15 bg-emerald-300/5 text-emerald-200";
}


// ============================================================
// PROFILE
// ============================================================

export default function CustomerProfilePage() {

  const params =
    useParams<{
      customerId: string;
    }>();


  const customerId =
    params.customerId;


  const [
    profile,
    setProfile,
  ] = useState<Profile | null>(
    null
  );


  const [
    loading,
    setLoading,
  ] = useState(true);


  const [
    error,
    setError,
  ] = useState<string | null>(
    null
  );


  // ==========================================================
  // LOAD
  // ==========================================================

  async function loadProfile() {

    try {

      setLoading(true);

      setError(null);


      const response =
        await getProfile(
          customerId
        );


      setProfile(
        response
      );

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load customer profile."
      );

    } finally {

      setLoading(false);

    }
  }


  useEffect(() => {

    if (
      customerId
    ) {
      loadProfile();
    }

  }, [
    customerId,
  ]);


  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {

    return (
      <main className="min-h-screen bg-[#07111f] text-white">

        <section className="mx-auto max-w-7xl px-6 py-12">

          <div className="animate-pulse">

            <div className="h-4 w-32 rounded bg-white/10" />

            <div className="mt-10 h-14 w-80 rounded bg-white/10" />

            <div className="mt-8 grid gap-4 md:grid-cols-4">

              {Array.from(
                {
                  length: 4,
                }
              ).map(
                (_, index) => (
                  <div
                    key={index}
                    className="h-36 rounded-3xl bg-white/[0.04]"
                  />
                )
              )}

            </div>

          </div>

        </section>

      </main>
    );
  }


  // ==========================================================
  // ERROR
  // ==========================================================

  if (
    error ||
    !profile
  ) {

    return (
      <main className="min-h-screen bg-[#07111f] text-white">

        <section className="mx-auto max-w-3xl px-6 py-24 text-center">

          <div className="mx-auto flex h-16 w-16 items-center justify-center rounded-3xl border border-red-300/15 bg-red-300/5">

            <XCircle className="h-7 w-7 text-red-300" />

          </div>

          <h1 className="mt-5 text-3xl font-semibold">
            Customer profile unavailable
          </h1>

          <p className="mt-3 text-sm text-white/40">
            {error ??
              "The requested customer profile could not be loaded."}
          </p>

          <div className="mt-7 flex justify-center gap-3">

            <Link
              href="/customers"
              className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm text-white/60 transition hover:bg-white/10 hover:text-white"
            >

              <ArrowLeft className="h-4 w-4" />

              Back to customers

            </Link>


            <button
              onClick={
                loadProfile
              }
              className="inline-flex items-center gap-2 rounded-2xl bg-cyan-300 px-5 py-3 text-sm font-medium text-[#07111f]"
            >

              <RefreshCw className="h-4 w-4" />

              Retry

            </button>

          </div>

        </section>

      </main>
    );
  }


  const repeatCustomer =
    profile.repeat_booking_flag >
    0;


  return (
    <main className="min-h-screen bg-[#07111f] text-white">

      {/* ======================================================
          AMBIENT BACKGROUND
          ====================================================== */}

      <div className="pointer-events-none fixed inset-0 overflow-hidden">

        <motion.div
          className="absolute -left-52 top-20 h-[34rem] w-[34rem] rounded-full bg-cyan-400/10 blur-3xl"
          animate={{
            x: [0, 55, 0],
            y: [0, 30, 0],
            scale: [1, 1.08, 1],
          }}
          transition={{
            duration: 13,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        <motion.div
          className="absolute right-[-140px] top-1/3 h-[30rem] w-[30rem] rounded-full bg-violet-500/10 blur-3xl"
          animate={{
            x: [0, -50, 0],
            y: [0, 40, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 15,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

      </div>


      {/* ======================================================
          MAIN
          ====================================================== */}

      <section className="relative z-10 mx-auto max-w-7xl px-6 py-10">

        {/* ====================================================
            TOP BAR
            ==================================================== */}

        <motion.div
          initial={{
            opacity: 0,
            y: 12,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          className="flex items-center justify-between"
        >

          <Link
            href="/customers"
            className="inline-flex items-center gap-2 text-sm text-white/40 transition hover:text-white"
          >

            <ArrowLeft className="h-4 w-4" />

            Customer intelligence

          </Link>


          <div className="flex items-center gap-2 rounded-full border border-cyan-300/10 bg-cyan-300/5 px-4 py-2 text-[10px] uppercase tracking-wider text-cyan-200/70">

            <Fingerprint className="h-3.5 w-3.5" />

            Forensic profile

          </div>

        </motion.div>


        {/* ====================================================
            PROFILE HERO
            ==================================================== */}

        <motion.section
          initial={{
            opacity: 0,
            y: 20,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            delay: 0.08,
          }}
          className="mt-8 rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl"
        >

          <div className="flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">

            <div className="flex items-center gap-5">

              <motion.div
                whileHover={{
                  scale: 1.04,
                }}
                className="relative flex h-20 w-20 shrink-0 items-center justify-center rounded-[1.6rem] border border-cyan-300/20 bg-cyan-300/10"
              >

                <UserRound className="h-8 w-8 text-cyan-300" />

              </motion.div>


              <div>

                <div className="flex flex-wrap items-center gap-3">

                  <h1 className="text-3xl font-semibold sm:text-4xl">
                    Customer {profile.customer_id}
                  </h1>


                  <span
                    className={`rounded-full border px-3 py-1 text-xs font-medium uppercase ${segmentClass(
                      profile.customer_segment
                    )}`}
                  >

                    {formatSegment(
                      profile.customer_segment
                    )}

                  </span>

                </div>


                <p className="mt-2 max-w-2xl text-sm leading-6 text-white/40">

                  {profile.segment_reason ||
                    "Validated customer intelligence profile."}

                </p>

              </div>

            </div>


            <div className="flex items-center gap-2 rounded-2xl border border-emerald-300/15 bg-emerald-300/5 px-4 py-3 text-emerald-200">

              <ShieldCheck className="h-4 w-4" />

              <div>

                <p className="text-xs font-medium">
                  Segmentation ready
                </p>

                <p className="mt-0.5 text-[10px] text-emerald-200/50">
                  Validated analytical profile
                </p>

              </div>

            </div>

          </div>

        </motion.section>


        {/* ====================================================
            CORE METRICS
            ==================================================== */}

        <div className="mt-5 grid gap-4 sm:grid-cols-2 xl:grid-cols-4">

          {[
            {
              label: "Total revenue",
              value: formatCurrency(
                profile.total_revenue
              ),
              icon: CircleDollarSign,
            },
            {
              label: "Total bookings",
              value:
                profile.total_bookings.toLocaleString(),
              icon: CalendarDays,
            },
            {
              label: "Average booking value",
              value: formatCurrency(
                profile.average_booking_value
              ),
              icon: BarChart3,
            },
            {
              label: "Recency",
              value:
                `${profile.recency_days} days`,
              icon: Clock3,
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
                    y: 18,
                  }}
                  animate={{
                    opacity: 1,
                    y: 0,
                  }}
                  transition={{
                    delay:
                      0.12 +
                      index *
                        0.06,
                  }}
                  whileHover={{
                    y: -4,
                  }}
                  className="rounded-3xl border border-white/10 bg-white/[0.04] p-5"
                >

                  <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/5">

                    <Icon className="h-5 w-5 text-cyan-300" />

                  </div>

                  <p className="mt-5 text-xs text-white/30">
                    {card.label}
                  </p>

                  <p className="mt-1 text-2xl font-semibold">
                    {card.value}
                  </p>

                </motion.div>

              );

            }
          )}

        </div>


        {/* ====================================================
            INTELLIGENCE
            ==================================================== */}

        <div className="mt-5 grid gap-5 lg:grid-cols-[1.35fr_0.65fr]">


          {/* ==================================================
              BEHAVIOR
              ================================================== */}

          <motion.section
            initial={{
              opacity: 0,
              x: -15,
            }}
            animate={{
              opacity: 1,
              x: 0,
            }}
            transition={{
              delay: 0.25,
            }}
            className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6"
          >

            <div className="flex items-center gap-2 text-sm text-white/45">

              <Gauge className="h-4 w-4 text-cyan-300" />

              Behavioral intelligence

            </div>


            <h2 className="mt-2 text-xl font-semibold">
              Customer behavior snapshot
            </h2>


            <div className="mt-6 grid gap-4 sm:grid-cols-2">


              <BehaviorCard
                label="Booking frequency"
                value={
                  profile.booking_frequency.toFixed(
                    4
                  )
                }
                icon={Activity}
              />


              <BehaviorCard
                label="Repeat customer"
                value={
                  repeatCustomer
                    ? "Yes"
                    : "No"
                }
                icon={RefreshCw}
                positive={
                  repeatCustomer
                }
              />


              <BehaviorCard
                label="Cohort month"
                value={
                  profile.cohort_month ??
                  "Not available"
                }
                icon={CalendarDays}
              />


              <BehaviorCard
                label="Exploratory cluster"
                value={
                  profile.cluster_id !==
                  null &&
                  profile.cluster_id !==
                  undefined
                    ? `Cluster ${profile.cluster_id}`
                    : "Not assigned"
                }
                icon={Layers3}
              />

            </div>


            {/* =================================================
                SEGMENT RATIONALE
                ================================================= */}

            <div className="mt-4 rounded-3xl border border-cyan-300/10 bg-cyan-300/[0.035] p-5">

              <div className="flex items-center gap-2 text-sm text-cyan-200/80">

                <Sparkles className="h-4 w-4" />

                Why this customer is segmented here

              </div>


              <p className="mt-3 text-sm leading-7 text-white/50">

                {profile.segment_reason ||
                  "No segment rationale was provided."}

              </p>

            </div>

          </motion.section>


          {/* ==================================================
              METADATA
              ================================================== */}

          <motion.section
            initial={{
              opacity: 0,
              x: 15,
            }}
            animate={{
              opacity: 1,
              x: 0,
            }}
            transition={{
              delay: 0.3,
            }}
            className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6"
          >

            <div className="flex items-center gap-2 text-sm text-white/45">

              <Fingerprint className="h-4 w-4 text-cyan-300" />

              Forensic metadata

            </div>


            <div className="mt-6 space-y-3">


              <MetadataRow
                label="Customer ID"
                value={
                  profile.customer_id
                }
                icon={UserRound}
              />


              <MetadataRow
                label="Segmentation method"
                value={segmentationMethodLabel(
                  profile.segmentation_method
                )}
                icon={Layers3}
              />


              <MetadataRow
                label="Profile status"
                value={
                  profile.segmentation_status
                }
                icon={ShieldCheck}
                positive
              />


              <MetadataRow
                label="Complaint coverage"
                value={
                  profile.complaint_segment_status
                }
                icon={ShieldCheck}
                className={complaintStatusClass(
                  profile.complaint_segment_status
                )}
              />

            </div>


            {/* TECHNICAL DETAILS */}

            <details className="mt-4 rounded-2xl border border-white/5 bg-black/10">

              <summary className="cursor-pointer px-4 py-3 text-xs text-white/35 transition hover:text-white/60">
                View technical segmentation metadata
              </summary>

              <div className="border-t border-white/5 px-4 py-4">

                <p className="break-words font-mono text-[10px] leading-5 text-white/25">

                  {profile.segmentation_method}

                </p>

              </div>

            </details>


            <div className="mt-4 rounded-2xl border border-emerald-300/10 bg-emerald-300/[0.025] p-4">

              <div className="flex items-center gap-2 text-xs text-emerald-200/70">

                <Zap className="h-3.5 w-3.5" />

                Data provenance

              </div>

              <p className="mt-2 text-xs leading-5 text-white/35">

                Derived from the validated Day 7
                final segmentation layer.

              </p>

            </div>

          </motion.section>

        </div>


        {/* ====================================================
            FOOTER ACTIONS
            ==================================================== */}

        <div className="mt-6 flex flex-wrap gap-3">

          <Link
            href="/customers"
            className="inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm text-white/55 transition hover:bg-white/10 hover:text-white"
          >

            <ArrowLeft className="h-4 w-4" />

            Back to all customers

          </Link>


          <Link
            href={`/journeys`}
            className="inline-flex items-center gap-2 rounded-2xl border border-cyan-300/10 bg-cyan-300/5 px-5 py-3 text-sm text-cyan-200/70 transition hover:bg-cyan-300/10 hover:text-cyan-200"
          >

            Investigate journeys

            <ArrowLeft className="h-4 w-4 rotate-180" />

          </Link>

        </div>

      </section>

    </main>
  );
}


// ============================================================
// BEHAVIOR CARD
// ============================================================

function BehaviorCard({
  label,
  value,
  icon: Icon,
  positive = false,
}: {
  label: string;
  value: string;
  icon: typeof Activity;
  positive?: boolean;
}) {

  return (
    <motion.div
      whileHover={{
        scale: 1.01,
      }}
      className="rounded-2xl border border-white/5 bg-black/10 p-4"
    >

      <div className="flex items-center gap-2">

        <Icon className="h-4 w-4 text-cyan-300/70" />

        <p className="text-xs text-white/30">
          {label}
        </p>

      </div>


      <p
        className={`mt-3 text-lg font-semibold ${
          positive
            ? "text-emerald-200"
            : "text-white"
        }`}
      >

        {value}

      </p>

    </motion.div>
  );
}


// ============================================================
// METADATA ROW
// ============================================================

function MetadataRow({
  label,
  value,
  icon: Icon,
  positive = false,
  className,
}: {
  label: string;
  value: string;
  icon: typeof Activity;
  positive?: boolean;
  className?: string;
}) {

  return (
    <div
      className={`rounded-2xl border border-white/5 bg-black/10 p-4 ${
        className ?? ""
      }`}
    >

      <div className="flex items-center gap-2">

        <Icon className="h-3.5 w-3.5 text-cyan-300/60" />

        <p className="text-[10px] uppercase tracking-wider text-white/25">
          {label}
        </p>

      </div>


      <p
        className={`mt-2 break-words text-sm font-medium ${
          positive
            ? "text-emerald-200"
            : ""
        }`}
      >

        {value}

      </p>

    </div>
  );
}