"use client";

import {
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  Database,
  FileWarning,
  Layers3,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  Table2,
  XCircle,
} from "lucide-react";

import { motion } from "motion/react";

import Link from "next/link";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getQuality,
  type QualityResponse,
  type QualityDataset,
} from "@/lib/api";


// ============================================================
// QUALITY STATUS
// ============================================================

function statusIcon(
  status: string
) {

  const normalized =
    status.toUpperCase();


  if (
    normalized === "EXCELLENT"
  ) {

    return (
      <CheckCircle2 className="h-4 w-4 text-emerald-300" />
    );
  }


  if (
    normalized === "WARNING" ||
    normalized === "WARN"
  ) {

    return (
      <AlertTriangle className="h-4 w-4 text-amber-300" />
    );
  }


  return (
    <XCircle className="h-4 w-4 text-red-300" />
  );
}


function statusClass(
  status: string
) {

  const normalized =
    status.toUpperCase();


  if (
    normalized === "EXCELLENT"
  ) {

    return "border-emerald-300/20 bg-emerald-300/10 text-emerald-200";
  }


  if (
    normalized === "WARNING" ||
    normalized === "WARN"
  ) {

    return "border-amber-300/20 bg-amber-300/10 text-amber-200";
  }


  return "border-red-300/20 bg-red-300/10 text-red-200";
}


// ============================================================
// QUALITY BAR
// ============================================================

function QualityBar({
  score,
}: {
  score: number;
}) {

  return (
    <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/5">

      <motion.div
        initial={{
          width: 0,
        }}
        animate={{
          width: `${Math.max(
            0,
            Math.min(
              100,
              score
            )
          )}%`,
        }}
        transition={{
          duration: 1,
          ease: "easeOut",
        }}
        className="h-full rounded-full bg-gradient-to-r from-cyan-300 via-blue-400 to-emerald-300"
      />

    </div>
  );
}


// ============================================================
// DATASET CARD
// ============================================================

function DatasetCard({
  dataset,
  index,
}: {
  dataset: QualityDataset;
  index: number;
}) {

  const hasMissing =
    dataset.missing_cells > 0;

  const hasDuplicates =
    dataset.duplicate_rows > 0;

  const hasInvalid =
    dataset.invalid_values > 0;


  return (
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
          index * 0.08,
        duration: 0.5,
      }}
      whileHover={{
        y: -4,
      }}
      className="group rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl"
    >

      {/* HEADER */}

      <div className="flex items-start justify-between gap-4">

        <div className="flex min-w-0 items-center gap-3">

          <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/5">

            <Database className="h-5 w-5 text-cyan-300" />

          </div>


          <div className="min-w-0">

            <p className="truncate font-semibold">
              {dataset.dataset}
            </p>

            <p className="mt-1 text-xs text-white/30">
              {dataset.rows.toLocaleString()} records ·{" "}
              {dataset.columns} columns
            </p>

          </div>

        </div>


        <div
          className={`flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-[10px] font-medium uppercase ${statusClass(
            dataset.quality_status
          )}`}
        >

          {statusIcon(
            dataset.quality_status
          )}

          {dataset.quality_status}

        </div>

      </div>


      {/* SCORE */}

      <div className="mt-7">

        <div className="flex items-end justify-between">

          <div>

            <p className="text-xs text-white/35">
              Quality score
            </p>

            <p className="mt-1 text-3xl font-semibold">
              {dataset.quality_score.toFixed(2)}%
            </p>

          </div>


          <div className="text-right">

            <p className="text-xs text-white/30">
              Row validation
            </p>

            <p className="mt-1 text-sm text-emerald-200">
              {dataset.row_count_status}
            </p>

          </div>

        </div>


        <QualityBar
          score={
            dataset.quality_score
          }
        />

      </div>


      {/* QUALITY SIGNALS */}

      <div className="mt-6 grid grid-cols-3 gap-3">

        <div className="rounded-2xl bg-black/10 p-3">

          <p className="text-[10px] text-white/30">
            Missing
          </p>

          <p
            className={`mt-1 text-sm font-medium ${
              hasMissing
                ? "text-amber-200"
                : "text-emerald-200"
            }`}
          >
            {dataset.missing_cells.toLocaleString()}
          </p>

        </div>


        <div className="rounded-2xl bg-black/10 p-3">

          <p className="text-[10px] text-white/30">
            Duplicates
          </p>

          <p
            className={`mt-1 text-sm font-medium ${
              hasDuplicates
                ? "text-amber-200"
                : "text-emerald-200"
            }`}
          >
            {dataset.duplicate_rows.toLocaleString()}
          </p>

        </div>


        <div className="rounded-2xl bg-black/10 p-3">

          <p className="text-[10px] text-white/30">
            Invalid
          </p>

          <p
            className={`mt-1 text-sm font-medium ${
              hasInvalid
                ? "text-red-200"
                : "text-emerald-200"
            }`}
          >
            {dataset.invalid_values.toLocaleString()}
          </p>

        </div>

      </div>


      {/* DETAILS */}

      <div className="mt-5 space-y-3">

        <div className="flex items-center justify-between text-xs">

          <span className="text-white/30">
            Missing percentage
          </span>

          <span className="text-white/65">
            {dataset.missing_percentage.toFixed(2)}%
          </span>

        </div>


        <div className="flex items-center justify-between text-xs">

          <span className="text-white/30">
            Duplicate percentage
          </span>

          <span className="text-white/65">
            {dataset.duplicate_percentage.toFixed(2)}%
          </span>

        </div>


        <div className="flex items-center justify-between text-xs">

          <span className="text-white/30">
            Invalid percentage
          </span>

          <span className="text-white/65">
            {dataset.invalid_percentage.toFixed(2)}%
          </span>

        </div>


        <div className="flex items-center justify-between text-xs">

          <span className="text-white/30">
            Columns with missing
          </span>

          <span className="text-white/65">
            {dataset.columns_with_missing}
          </span>

        </div>

      </div>


      {/* CARD FOOTER */}

      <div className="mt-6 flex items-center gap-2 text-[11px] text-white/25">

        {hasMissing ? (
          <>
            <FileWarning className="h-3.5 w-3.5 text-amber-300" />
            Missing-value attention detected
          </>
        ) : (
          <>
            <ShieldCheck className="h-3.5 w-3.5 text-emerald-300" />
            No missing-value issue detected
          </>
        )}

      </div>

    </motion.div>
  );
}


// ============================================================
// PAGE
// ============================================================

export default function QualityPage() {

  const [data, setData] =
    useState<QualityResponse | null>(
      null
    );


  const [loading, setLoading] =
    useState(true);


  const [error, setError] =
    useState<string | null>(
      null
    );


  const [
    selectedDataset,
    setSelectedDataset,
  ] = useState<string | null>(
    null
  );


  // ==========================================================
  // LOAD QUALITY
  // ==========================================================

  async function loadQuality() {

    try {

      setLoading(true);

      const response =
        await getQuality();

      setData(
        response
      );

      setError(
        null
      );

    } catch (err) {

      setError(
        err instanceof Error
          ? err.message
          : "Unable to load data quality report."
      );

    } finally {

      setLoading(false);

    }
  }


  useEffect(() => {

    loadQuality();

  }, []);


  // ==========================================================
  // SELECTED DATASET
  // ==========================================================

  const selected =
    useMemo(() => {

      if (!data || !selectedDataset) {
        return null;
      }


      return (
        data.datasets.find(
          (dataset) =>
            dataset.dataset ===
            selectedDataset
        ) ?? null
      );

    }, [
      data,
      selectedDataset,
    ]);


  // ==========================================================
  // LOADING
  // ==========================================================

  if (loading) {

    return (

      <main className="min-h-screen bg-[#07111f] text-white">

        <div className="mx-auto max-w-7xl px-6 py-12">

          <div className="h-8 w-52 animate-pulse rounded-xl bg-white/10" />

          <div className="mt-8 grid gap-5 md:grid-cols-3">

            {Array.from(
              {
                length: 6,
              }
            ).map(
              (_, index) => (

                <div
                  key={index}
                  className="h-80 animate-pulse rounded-[2rem] bg-white/[0.04]"
                />

              )
            )}

          </div>

        </div>

      </main>
    );
  }


  // ==========================================================
  // ERROR
  // ==========================================================

  if (error || !data) {

    return (

      <main className="min-h-screen bg-[#07111f] text-white">

        <div className="mx-auto max-w-3xl px-6 py-24 text-center">

          <XCircle className="mx-auto h-12 w-12 text-red-300" />

          <h1 className="mt-5 text-3xl font-semibold">
            Data quality unavailable
          </h1>

          <p className="mt-3 text-white/40">
            {error ??
              "Unable to retrieve the quality report."}
          </p>


          <button
            onClick={
              loadQuality
            }
            className="mt-7 inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm text-white/70 transition hover:bg-white/10"
          >

            <RefreshCw className="h-4 w-4" />

            Retry

          </button>

        </div>

      </main>
    );
  }


  return (

    <main className="min-h-screen bg-[#07111f] text-white">


      {/* ======================================================
          AMBIENT BACKGROUND
          ====================================================== */}

      <div className="pointer-events-none fixed inset-0 overflow-hidden">

        <motion.div
          className="absolute -left-40 top-20 h-[30rem] w-[30rem] rounded-full bg-cyan-400/10 blur-3xl"
          animate={{
            x: [0, 60, 0],
            y: [0, 30, 0],
          }}
          transition={{
            duration: 12,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />


        <motion.div
          className="absolute right-[-140px] top-1/3 h-[32rem] w-[32rem] rounded-full bg-violet-500/10 blur-3xl"
          animate={{
            x: [0, -50, 0],
            y: [0, 50, 0],
          }}
          transition={{
            duration: 14,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

      </div>


      {/* ======================================================
          NAV
          ====================================================== */}

      <nav className="relative z-10 border-b border-white/10 bg-[#07111f]/75 backdrop-blur-xl">

        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">

          <Link
            href="/"
            className="flex items-center gap-3"
          >

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10">

              <Table2 className="h-5 w-5 text-cyan-300" />

            </div>


            <div>

              <p className="text-sm font-semibold tracking-[0.22em]">
                JOURNEY
              </p>

              <p className="text-xs tracking-[0.3em] text-cyan-300/70">
                FORENSICS
              </p>

            </div>

          </Link>


          <div className="flex items-center gap-2 rounded-full border border-emerald-300/10 bg-emerald-300/5 px-4 py-2 text-xs text-emerald-200/80">

            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />

            Data quality monitor

          </div>

        </div>

      </nav>


      {/* ======================================================
          CONTENT
          ====================================================== */}

      <section className="relative z-10 mx-auto max-w-7xl px-6 py-12">


        {/* HEADER */}

        <motion.div
          initial={{
            opacity: 0,
            y: 20,
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


          <div className="mt-8 flex flex-col gap-7 lg:flex-row lg:items-end lg:justify-between">

            <div>

              <div className="flex items-center gap-2 text-cyan-300/70">

                <Sparkles className="h-4 w-4" />

                Data quality intelligence

              </div>


              <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">

                Know your data.

                <span className="block bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400 bg-clip-text text-transparent">

                  Before it knows you.

                </span>

              </h1>


              <p className="mt-4 max-w-2xl text-base leading-7 text-white/45">

                A forensic view of dataset completeness,
                duplication, validity, cardinality and
                structural quality across the analytics
                foundation.

              </p>

            </div>


            <button
              onClick={
                loadQuality
              }
              className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm text-white/60 transition hover:bg-white/10 hover:text-white"
            >

              <RefreshCw className="h-4 w-4" />

              Refresh report

            </button>

          </div>

        </motion.div>


        {/* ====================================================
            TOP METRICS
            ==================================================== */}

        <div className="mt-9 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">


          {/* OVERALL SCORE */}

          <motion.div
            initial={{
              opacity: 0,
              y: 18,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            className="rounded-[2rem] border border-cyan-300/10 bg-cyan-300/[0.035] p-6 backdrop-blur-xl"
          >

            <div className="flex items-center justify-between">

              <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-cyan-300/10">

                <ShieldCheck className="h-5 w-5 text-cyan-300" />

              </div>


              <Sparkles className="h-4 w-4 text-cyan-300/40" />

            </div>


            <p className="mt-6 text-xs text-white/35">
              Overall quality
            </p>


            <p className="mt-1 text-4xl font-semibold">
              {data.overall_quality_score.toFixed(2)}%
            </p>


            <QualityBar
              score={
                data.overall_quality_score
              }
            />

          </motion.div>


          {/* DATASETS */}

          <motion.div
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
            className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl"
          >

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/5">

              <Database className="h-5 w-5 text-cyan-300" />

            </div>


            <p className="mt-6 text-xs text-white/35">
              Datasets analyzed
            </p>


            <p className="mt-1 text-4xl font-semibold">
              {data.total_datasets}
            </p>


            <p className="mt-2 text-xs text-emerald-200/70">
              {data.excellent_datasets} excellent
            </p>

          </motion.div>


          {/* MISSING */}

          <motion.div
            initial={{
              opacity: 0,
              y: 18,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              delay: 0.16,
            }}
            className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl"
          >

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/5">

              <FileWarning className="h-5 w-5 text-amber-300" />

            </div>


            <p className="mt-6 text-xs text-white/35">
              Missing cells
            </p>


            <p className="mt-1 text-4xl font-semibold">
              {data.total_missing_cells.toLocaleString()}
            </p>


            <p className="mt-2 text-xs text-amber-200/70">
              Concentrated in payment data
            </p>

          </motion.div>


          {/* INVALID */}

          <motion.div
            initial={{
              opacity: 0,
              y: 18,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            transition={{
              delay: 0.24,
            }}
            className="rounded-[2rem] border border-white/10 bg-white/[0.04] p-6 backdrop-blur-xl"
          >

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/5">

              <BarChart3 className="h-5 w-5 text-emerald-300" />

            </div>


            <p className="mt-6 text-xs text-white/35">
              Invalid values
            </p>


            <p className="mt-1 text-4xl font-semibold">
              {data.total_invalid_values.toLocaleString()}
            </p>


            <p className="mt-2 text-xs text-emerald-200/70">
              No invalid values detected
            </p>

          </motion.div>

        </div>


        {/* ====================================================
            SUMMARY
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
          transition={{
            delay: 0.3,
          }}
          className="mt-5 rounded-[2rem] border border-white/10 bg-white/[0.035] p-6 backdrop-blur-xl"
        >

          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">

            <div>

              <div className="flex items-center gap-2 text-sm text-white/45">

                <Layers3 className="h-4 w-4 text-cyan-300" />

                Quality posture

              </div>


              <h2 className="mt-2 text-xl font-semibold">
                Your analytical foundation is strong.
              </h2>


              <p className="mt-2 max-w-3xl text-sm leading-6 text-white/35">

                Four datasets are fully clean. The only
                material quality signal is missing payment
                data, while duplicate and invalid-value checks
                remain clean.

              </p>

            </div>


            <div className="flex flex-wrap gap-3">

              <div className="rounded-2xl border border-emerald-300/15 bg-emerald-300/5 px-4 py-3">

                <p className="text-[10px] uppercase tracking-wider text-white/30">
                  Excellent
                </p>

                <p className="mt-1 text-xl font-semibold text-emerald-200">
                  {data.excellent_datasets}
                </p>

              </div>


              <div className="rounded-2xl border border-amber-300/15 bg-amber-300/5 px-4 py-3">

                <p className="text-[10px] uppercase tracking-wider text-white/30">
                  Warning
                </p>

                <p className="mt-1 text-xl font-semibold text-amber-200">
                  {data.warning_datasets}
                </p>

              </div>


              <div className="rounded-2xl border border-red-300/15 bg-red-300/5 px-4 py-3">

                <p className="text-[10px] uppercase tracking-wider text-white/30">
                  Failed
                </p>

                <p className="mt-1 text-xl font-semibold text-red-200">
                  {data.failed_datasets}
                </p>

              </div>

            </div>

          </div>

        </motion.div>


        {/* ====================================================
            DATASETS
            ==================================================== */}

        <div className="mt-9">

          <div className="mb-5">

            <p className="text-sm text-cyan-300/70">
              Dataset diagnostics
            </p>

            <h2 className="mt-1 text-2xl font-semibold">
              Quality by dataset
            </h2>

          </div>


          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">

            {data.datasets.map(
              (
                dataset,
                index
              ) => (

                <button
                  type="button"
                  key={dataset.dataset}
                  onClick={() =>
                    setSelectedDataset(
                      dataset.dataset
                    )
                  }
                  className="text-left"
                >

                  <DatasetCard
                    dataset={dataset}
                    index={index}
                  />

                </button>

              )
            )}

          </div>

        </div>


        {/* ====================================================
            SELECTED DATASET DETAIL
            ==================================================== */}

        {selected && (

          <motion.div
            initial={{
              opacity: 0,
              y: 20,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            className="mt-8 rounded-[2rem] border border-cyan-300/10 bg-cyan-300/[0.025] p-7 backdrop-blur-xl"
          >

            <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">

              <div>

                <p className="text-sm text-cyan-300/70">
                  Detailed dataset inspection
                </p>

                <h2 className="mt-1 text-2xl font-semibold">
                  {selected.dataset}
                </h2>

              </div>


              <button
                onClick={() =>
                  setSelectedDataset(
                    null
                  )
                }
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs text-white/50 transition hover:bg-white/10 hover:text-white"
              >
                Close
              </button>

            </div>


            <div className="mt-7 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

              {[
                [
                  "Rows",
                  selected.rows.toLocaleString(),
                ],
                [
                  "Expected rows",
                  selected.expected_rows.toLocaleString(),
                ],
                [
                  "Columns",
                  selected.columns.toString(),
                ],
                [
                  "Unique values",
                  selected.unique_values.toLocaleString(),
                ],
                [
                  "Cardinality",
                  `${selected.cardinality_percentage.toFixed(2)}%`,
                ],
                [
                  "Numeric columns",
                  selected.numeric_columns.toString(),
                ],
                [
                  "Datetime columns",
                  selected.datetime_like_columns.toString(),
                ],
                [
                  "Missing columns",
                  selected.columns_with_missing.toString(),
                ],
              ].map(
                (
                  [label, value]
                ) => (

                  <div
                    key={label}
                    className="rounded-2xl border border-white/5 bg-black/10 p-4"
                  >

                    <p className="text-[10px] text-white/30">
                      {label}
                    </p>

                    <p className="mt-2 text-lg font-medium">
                      {value}
                    </p>

                  </div>

                )
              )}

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
            Data quality intelligence
          </span>

        </div>

      </footer>

    </main>
  );
}