"use client";

import type { ReactNode } from "react";

import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  Database,
  FileWarning,
  Info,
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
  useCallback,
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getQuality,
  type QualityDataset,
  type QualityResponse,
} from "@/lib/api";


/* ============================================================
   QUALITY STATUS ICON
   ============================================================ */

function statusIcon(
  status: string,
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


/* ============================================================
   QUALITY STATUS CLASS
   ============================================================ */

function statusClass(
  status: string,
) {

  const normalized =
    status.toUpperCase();


  if (
    normalized === "EXCELLENT"
  ) {

    return (
      "border-emerald-300/20 " +
      "bg-emerald-300/10 " +
      "text-emerald-200"
    );
  }


  if (
    normalized === "WARNING" ||
    normalized === "WARN"
  ) {

    return (
      "border-amber-300/20 " +
      "bg-amber-300/10 " +
      "text-amber-200"
    );
  }


  return (
    "border-red-300/20 " +
    "bg-red-300/10 " +
    "text-red-200"
  );
}


/* ============================================================
   QUALITY BAR
   ============================================================ */

function QualityBar({
  score,
}: {
  score: number;
}) {

  const safeScore =
    Math.max(
      0,
      Math.min(
        100,
        score,
      ),
    );


  return (

    <div className="mt-4 h-2 overflow-hidden rounded-full bg-white/5">

      <motion.div
        initial={{
          width: 0,
        }}
        animate={{
          width:
            `${safeScore}%`,
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


/* ============================================================
   DATASET CARD
   ============================================================ */

function DatasetCard({
  dataset,
  index,
  onSelect,
}: {
  dataset: QualityDataset;
  index: number;
  onSelect: () => void;
}) {

  const hasMissing =
    dataset.missing_cells > 0;


  const hasDuplicates =
    dataset.duplicate_rows > 0;


  const hasInvalid =
    dataset.invalid_values > 0;


  return (

    <motion.button
      type="button"
      onClick={onSelect}
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
          index * 0.07,
        duration: 0.45,
      }}
      whileHover={{
        y: -4,
      }}
      className="group w-full text-left"
    >

      <div className="relative h-full overflow-hidden rounded-[2rem] border border-white/10 bg-[#101b2a]/80 p-6 backdrop-blur-xl transition group-hover:border-cyan-300/15 group-hover:bg-[#101b2a]/90">

        <div className="pointer-events-none absolute -right-16 -top-16 h-36 w-36 rounded-full bg-cyan-300/[0.035] blur-3xl transition group-hover:bg-cyan-300/[0.06]" />


        {/* HEADER */}

        <div className="relative flex items-start justify-between gap-4">

          <div className="flex min-w-0 items-center gap-3">

            <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl border border-white/5 bg-white/[0.04]">

              <Database className="h-5 w-5 text-cyan-300" />

            </div>


            <div className="min-w-0">

              <p className="truncate font-semibold text-white/90">
                {dataset.dataset}
              </p>


              <p className="mt-1 text-xs text-white/30">

                {dataset.rows.toLocaleString()}
                {" "}records ·{" "}
                {dataset.columns}
                {" "}columns

              </p>

            </div>

          </div>


          <div
            className={`flex shrink-0 items-center gap-2 rounded-full border px-3 py-1.5 text-[10px] font-medium uppercase ${statusClass(
              dataset.quality_status,
            )}`}
          >

            {statusIcon(
              dataset.quality_status,
            )}

            {dataset.quality_status}

          </div>

        </div>


        {/* SCORE */}

        <div className="relative mt-7">

          <div className="flex items-end justify-between gap-4">

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


        {/* SIGNALS */}

        <div className="relative mt-6 grid grid-cols-3 gap-3">

          <SignalBox
            label="Missing"
            value={
              dataset.missing_cells.toLocaleString()
            }
            warning={
              hasMissing
            }
          />


          <SignalBox
            label="Duplicates"
            value={
              dataset.duplicate_rows.toLocaleString()
            }
            warning={
              hasDuplicates
            }
          />


          <SignalBox
            label="Invalid"
            value={
              dataset.invalid_values.toLocaleString()
            }
            warning={
              hasInvalid
            }
            danger={
              hasInvalid
            }
          />

        </div>


        {/* DETAIL */}

        <div className="relative mt-5 space-y-3">

          <DetailRow
            label="Missing percentage"
            value={
              `${dataset.missing_percentage.toFixed(2)}%`
            }
          />


          <DetailRow
            label="Duplicate percentage"
            value={
              `${dataset.duplicate_percentage.toFixed(2)}%`
            }
          />


          <DetailRow
            label="Invalid percentage"
            value={
              `${dataset.invalid_percentage.toFixed(2)}%`
            }
          />


          <DetailRow
            label="Columns with missing"
            value={
              dataset.columns_with_missing.toString()
            }
          />

        </div>


        {/* FOOTER */}

        <div className="relative mt-6 flex items-center justify-between border-t border-white/5 pt-4 text-[11px]">

          <span className="flex items-center gap-2 text-white/30">

            {hasInvalid ? (
              <>
                <XCircle className="h-3.5 w-3.5 text-red-300" />
                Invalid-value attention
              </>
            ) : hasMissing || hasDuplicates ? (
              <>
                <AlertTriangle className="h-3.5 w-3.5 text-amber-300" />
                Data-quality attention
              </>
            ) : (
              <>
                <ShieldCheck className="h-3.5 w-3.5 text-emerald-300" />
                No material issue detected
              </>
            )}

          </span>


          <span className="text-cyan-300/50 transition group-hover:text-cyan-200">
            Inspect →
          </span>

        </div>

      </div>

    </motion.button>
  );
}


/* ============================================================
   SIGNAL BOX
   ============================================================ */

function SignalBox({
  label,
  value,
  warning,
  danger = false,
}: {
  label: string;
  value: string;
  warning: boolean;
  danger?: boolean;
}) {

  const textClass =
    danger
      ? "text-red-200"
      : warning
        ? "text-amber-200"
        : "text-emerald-200";


  return (

    <div className="rounded-2xl border border-white/5 bg-black/10 p-3">

      <p className="text-[10px] text-white/30">
        {label}
      </p>


      <p
        className={`mt-1 text-sm font-medium ${textClass}`}
      >
        {value}
      </p>

    </div>
  );
}


/* ============================================================
   DETAIL ROW
   ============================================================ */

function DetailRow({
  label,
  value,
}: {
  label: string;
  value: string;
}) {

  return (

    <div className="flex items-center justify-between gap-4 text-xs">

      <span className="text-white/30">
        {label}
      </span>


      <span className="text-white/65">
        {value}
      </span>

    </div>
  );
}


/* ============================================================
   PAGE
   ============================================================ */

export default function QualityPage() {

  const [
    data,
    setData,
  ] = useState<QualityResponse | null>(
    null,
  );


  const [
    loading,
    setLoading,
  ] = useState<boolean>(
    true,
  );


  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  const [
    selectedDataset,
    setSelectedDataset,
  ] = useState<string | null>(
    null,
  );


  /* ==========================================================
     LOAD QUALITY
     ========================================================== */

  const loadQuality =
    useCallback(
      async (): Promise<void> => {

        try {

          setLoading(
            true,
          );


          const response =
            await getQuality();


          setData(
            response,
          );


          setError(
            null,
          );

        } catch (
          err
        ) {

          setError(
            err instanceof Error
              ? err.message
              : "Unable to load data quality report.",
          );

        } finally {

          setLoading(
            false,
          );
        }

      },
      [],
    );


  useEffect(() => {

    // The initial data load intentionally updates state
    // after the asynchronous API request completes.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadQuality();

  }, [
    loadQuality,
  ]);


  /* ==========================================================
     SELECTED DATASET
     ========================================================== */

  const selected =
    useMemo(
      () => {

        if (
          !data ||
          !selectedDataset
        ) {

          return null;
        }


        return (
          data.datasets.find(
            (
              dataset,
            ) =>
              dataset.dataset ===
              selectedDataset,
          ) ??
          null
        );

      },
      [
        data,
        selectedDataset,
      ],
    );


  /* ==========================================================
     LOADING
     ========================================================== */

  if (loading) {

    return (

      <main className="relative min-h-screen overflow-hidden bg-[#07111f] text-white">

        <AmbientBackground />


        <section className="relative z-10 mx-auto max-w-7xl px-6 py-12">

          <div className="h-4 w-40 animate-pulse rounded-full bg-white/10" />


          <div className="mt-5 h-10 w-72 animate-pulse rounded-xl bg-white/10" />


          <div className="mt-3 h-5 w-[30rem] max-w-full animate-pulse rounded-xl bg-white/5" />


          <div className="mt-10 grid gap-5 md:grid-cols-2 xl:grid-cols-3">

            {Array.from({
              length: 6,
            }).map(
              (
                _,
                index,
              ) => (

                <div
                  key={
                    index
                  }
                  className="h-[440px] animate-pulse rounded-[2rem] bg-white/[0.035]"
                />

              ),
            )}

          </div>

        </section>

      </main>
    );
  }


  /* ==========================================================
     ERROR
     ========================================================== */

  if (
    error ||
    !data
  ) {

    return (

      <main className="relative min-h-screen overflow-hidden bg-[#07111f] text-white">

        <AmbientBackground />


        <section className="relative z-10 mx-auto max-w-3xl px-6 py-24 text-center">

          <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-red-300/10">

            <XCircle className="h-7 w-7 text-red-300" />

          </div>


          <h1 className="mt-5 text-3xl font-semibold">

            Data quality unavailable

          </h1>


          <p className="mt-3 text-white/40">

            {error ??
              "Unable to retrieve the quality report."}

          </p>


          <button
            type="button"
            onClick={() =>
              void loadQuality()
            }
            className="mt-7 inline-flex items-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm text-white/70 transition hover:bg-white/10 hover:text-white"
          >

            <RefreshCw className="h-4 w-4" />

            Retry

          </button>

        </section>

      </main>
    );
  }


  /* ==========================================================
     DYNAMIC QUALITY COUNTS
     ========================================================== */

  const warningOrFailed =
    data.warning_datasets +
    data.failed_datasets;


  const hasQualityConcerns =
    warningOrFailed > 0;


  /* ==========================================================
     RENDER
     ========================================================== */

  return (

    <main className="relative min-h-screen overflow-hidden bg-[#07111f] text-white">

      <AmbientBackground />


      {/* ======================================================
          CONTENT
          ====================================================== */}

      <section className="relative z-10 mx-auto max-w-7xl px-6 py-12">


        {/* ====================================================
            HEADER
            ==================================================== */}

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

              <div className="flex items-center gap-2 text-cyan-300/75">

                <Sparkles className="h-4 w-4" />

                Data quality intelligence

              </div>


              <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">

                Know your data.

                <span className="block bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400 bg-clip-text text-transparent">

                  Before it drives decisions.

                </span>

              </h1>


              <p className="mt-4 max-w-3xl text-base leading-7 text-white/45">

                Inspect completeness, duplication,
                validity, cardinality and structural
                quality across the analytics foundation.

              </p>

            </div>


            <button
              type="button"
              onClick={() =>
                void loadQuality()
              }
              className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm text-white/60 transition hover:bg-white/10 hover:text-white"
            >

              <RefreshCw className="h-4 w-4" />

              Refresh report

            </button>

          </div>

        </motion.div>


        {/* ====================================================
            QUALITY SUMMARY
            ==================================================== */}

        <div className="mt-9 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">


          {/* OVERALL */}

          <SummaryCard
            icon={
              <ShieldCheck className="h-5 w-5 text-cyan-300" />
            }
            label="Overall quality"
            value={
              `${data.overall_quality_score.toFixed(2)}%`
            }
            caption={
              hasQualityConcerns
                ? "Quality attention present"
                : "Healthy quality posture"
            }
            delay={0}
          />


          {/* DATASETS */}

          <SummaryCard
            icon={
              <Database className="h-5 w-5 text-cyan-300" />
            }
            label="Datasets analyzed"
            value={
              data.total_datasets.toLocaleString()
            }
            caption={
              `${data.excellent_datasets} excellent`
            }
            delay={0.07}
          />


          {/* MISSING */}

          <SummaryCard
            icon={
              <FileWarning className="h-5 w-5 text-amber-300" />
            }
            label="Missing cells"
            value={
              data.total_missing_cells.toLocaleString()
            }
            caption={
              data.total_missing_cells > 0
                ? "Missing-value signal detected"
                : "No missing cells"
            }
            delay={0.14}
          />


          {/* INVALID */}

          <SummaryCard
            icon={
              <BarChart3 className="h-5 w-5 text-emerald-300" />
            }
            label="Invalid values"
            value={
              data.total_invalid_values.toLocaleString()
            }
            caption={
              data.total_invalid_values > 0
                ? "Invalid-value signal detected"
                : "No invalid values"
            }
            delay={0.21}
          />

        </div>


        {/* ====================================================
            QUALITY POSTURE
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
            delay: 0.26,
          }}
          className="mt-5 rounded-[2rem] border border-white/10 bg-[#101b2a]/75 p-6 backdrop-blur-xl"
        >

          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">

            <div className="flex items-start gap-4">

              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/5">

                <Layers3 className="h-5 w-5 text-cyan-300" />

              </div>


              <div>

                <p className="text-sm font-semibold text-white/85">
                  Quality posture
                </p>


                <p className="mt-1 max-w-3xl text-sm leading-6 text-white/35">

                  {hasQualityConcerns
                    ? `${warningOrFailed} dataset${warningOrFailed === 1 ? "" : "s"} require${warningOrFailed === 1 ? "s" : ""} attention. Review the affected dataset cards below for the underlying signals.`
                    : "All analyzed datasets are currently within their reported quality-status thresholds."}

                </p>

              </div>

            </div>


            <div className="flex shrink-0 flex-wrap gap-3">

              <MiniStatus
                label="Excellent"
                value={
                  data.excellent_datasets
                }
                tone="emerald"
              />


              <MiniStatus
                label="Warning"
                value={
                  data.warning_datasets
                }
                tone="amber"
              />


              <MiniStatus
                label="Failed"
                value={
                  data.failed_datasets
                }
                tone="red"
              />

            </div>

          </div>

        </motion.div>


        {/* ====================================================
            DATASET SECTION
            ==================================================== */}

        <div className="mt-10">

          <div className="mb-5 flex items-end justify-between gap-4">

            <div>

              <div className="flex items-center gap-2 text-cyan-300/70">

                <Table2 className="h-4 w-4" />

                Dataset diagnostics

              </div>


              <h2 className="mt-1 text-2xl font-semibold">
                Quality by dataset
              </h2>

            </div>


            <p className="hidden text-xs text-white/25 sm:block">
              Select a dataset for detailed inspection
            </p>

          </div>


          <div className="grid gap-5 md:grid-cols-2 xl:grid-cols-3">

            {data.datasets.map(
              (
                dataset,
                index,
              ) => (

                <DatasetCard
                  key={
                    dataset.dataset
                  }
                  dataset={
                    dataset
                  }
                  index={
                    index
                  }
                  onSelect={() =>
                    setSelectedDataset(
                      dataset.dataset,
                    )
                  }
                />

              ),
            )}

          </div>

        </div>


        {/* ====================================================
            DETAIL PANEL
            ==================================================== */}

        {selected && (

          <motion.section
            initial={{
              opacity: 0,
              y: 20,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            className="mt-8 overflow-hidden rounded-[2rem] border border-cyan-300/10 bg-[#0d1928]/90 p-7 backdrop-blur-xl"
          >

            <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">

              <div>

                <div className="flex items-center gap-2 text-sm text-cyan-300/70">

                  <Activity className="h-4 w-4" />

                  Detailed dataset inspection

                </div>


                <h2 className="mt-2 text-2xl font-semibold">
                  {selected.dataset}
                </h2>

              </div>


              <button
                type="button"
                onClick={() =>
                  setSelectedDataset(
                    null,
                  )
                }
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs text-white/50 transition hover:bg-white/10 hover:text-white"
              >

                Close

              </button>

            </div>


            {/* SCORE */}

            <div className="mt-7 rounded-3xl border border-white/5 bg-black/10 p-5">

              <div className="flex flex-col gap-4 sm:flex-row sm:items-end sm:justify-between">

                <div>

                  <p className="text-xs text-white/30">
                    Quality score
                  </p>


                  <p className="mt-1 text-4xl font-semibold">
                    {selected.quality_score.toFixed(2)}%
                  </p>

                </div>


                <div
                  className={`flex w-fit items-center gap-2 rounded-full border px-3 py-1.5 text-xs uppercase ${statusClass(
                    selected.quality_status,
                  )}`}
                >

                  {statusIcon(
                    selected.quality_status,
                  )}

                  {selected.quality_status}

                </div>

              </div>


              <QualityBar
                score={
                  selected.quality_score
                }
              />

            </div>


            {/* METRICS */}

            <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

              <InspectionMetric
                label="Rows"
                value={
                  selected.rows.toLocaleString()
                }
              />


              <InspectionMetric
                label="Expected rows"
                value={
                  selected.expected_rows.toLocaleString()
                }
              />


              <InspectionMetric
                label="Columns"
                value={
                  selected.columns.toString()
                }
              />


              <InspectionMetric
                label="Unique values"
                value={
                  selected.unique_values.toLocaleString()
                }
              />


              <InspectionMetric
                label="Cardinality"
                value={
                  `${selected.cardinality_percentage.toFixed(2)}%`
                }
              />


              <InspectionMetric
                label="Numeric columns"
                value={
                  selected.numeric_columns.toString()
                }
              />


              <InspectionMetric
                label="Datetime-like columns"
                value={
                  selected.datetime_like_columns.toString()
                }
              />


              <InspectionMetric
                label="Columns with missing"
                value={
                  selected.columns_with_missing.toString()
                }
              />

            </div>


            {/* QUALITY SIGNALS */}

            <div className="mt-5 grid gap-4 lg:grid-cols-3">

              <InspectionSignal
                title="Missing values"
                value={
                  selected.missing_cells.toLocaleString()
                }
                percentage={
                  `${selected.missing_percentage.toFixed(2)}%`
                }
                tone={
                  selected.missing_cells > 0
                    ? "amber"
                    : "emerald"
                }
              />


              <InspectionSignal
                title="Duplicate rows"
                value={
                  selected.duplicate_rows.toLocaleString()
                }
                percentage={
                  `${selected.duplicate_percentage.toFixed(2)}%`
                }
                tone={
                  selected.duplicate_rows > 0
                    ? "amber"
                    : "emerald"
                }
              />


              <InspectionSignal
                title="Invalid values"
                value={
                  selected.invalid_values.toLocaleString()
                }
                percentage={
                  `${selected.invalid_percentage.toFixed(2)}%`
                }
                tone={
                  selected.invalid_values > 0
                    ? "red"
                    : "emerald"
                }
              />

            </div>


            {/* STRUCTURE */}

            <div className="mt-5 rounded-3xl border border-white/5 bg-black/10 p-5">

              <div className="flex items-center gap-2 text-sm text-cyan-200/80">

                <Info className="h-4 w-4" />

                Structural profile

              </div>


              <div className="mt-4 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">

                <InspectionMetric
                  label="Object columns"
                  value={
                    selected.object_columns.toString()
                  }
                />


                <InspectionMetric
                  label="String columns"
                  value={
                    selected.string_columns.toString()
                  }
                />


                <InspectionMetric
                  label="Numeric columns"
                  value={
                    selected.numeric_columns.toString()
                  }
                />


                <InspectionMetric
                  label="Datetime-like columns"
                  value={
                    selected.datetime_like_columns.toString()
                  }
                />

              </div>

            </div>

          </motion.section>

        )}

      </section>


      {/* ======================================================
          FOOTER
          ====================================================== */}

      <footer className="relative z-10 border-t border-white/10 px-6 py-6">

        <div className="mx-auto flex max-w-7xl items-center justify-between text-xs text-white/25">

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


/* ============================================================
   SUMMARY CARD
   ============================================================ */

function SummaryCard({
  icon,
  label,
  value,
  caption,
  delay,
}: {
  icon: ReactNode;
  label: string;
  value: string;
  caption: string;
  delay: number;
}) {

  return (

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
        delay,
        duration: 0.45,
      }}
      whileHover={{
        y: -4,
      }}
      className="group relative overflow-hidden rounded-[2rem] border border-white/10 bg-[#101b2a]/80 p-6 backdrop-blur-xl"
    >

      <div className="pointer-events-none absolute -right-10 -top-10 h-24 w-24 rounded-full bg-cyan-300/[0.035] blur-2xl transition group-hover:bg-cyan-300/[0.06]" />


      <div className="relative">

        <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-white/5">

          {icon}

        </div>


        <p className="mt-6 text-xs text-white/35">
          {label}
        </p>


        <p className="mt-1 text-4xl font-semibold">
          {value}
        </p>


        <p className="mt-2 text-xs text-white/35">
          {caption}
        </p>

      </div>

    </motion.div>
  );
}


/* ============================================================
   MINI STATUS
   ============================================================ */

function MiniStatus({
  label,
  value,
  tone,
}: {
  label: string;
  value: number;
  tone: "emerald" | "amber" | "red";
}) {

  const classes = {
    emerald:
      "border-emerald-300/15 bg-emerald-300/5 text-emerald-200",
    amber:
      "border-amber-300/15 bg-amber-300/5 text-amber-200",
    red:
      "border-red-300/15 bg-red-300/5 text-red-200",
  };


  return (

    <div
      className={`rounded-2xl border px-4 py-3 ${classes[tone]}`}
    >

      <p className="text-[10px] uppercase tracking-wider text-white/30">
        {label}
      </p>


      <p className="mt-1 text-xl font-semibold">
        {value}
      </p>

    </div>
  );
}


/* ============================================================
   INSPECTION METRIC
   ============================================================ */

function InspectionMetric({
  label,
  value,
}: {
  label: string;
  value: string;
}) {

  return (

    <div className="rounded-2xl border border-white/5 bg-black/10 p-4">

      <p className="text-[10px] text-white/30">
        {label}
      </p>


      <p className="mt-2 text-lg font-medium text-white/85">
        {value}
      </p>

    </div>
  );
}


/* ============================================================
   INSPECTION SIGNAL
   ============================================================ */

function InspectionSignal({
  title,
  value,
  percentage,
  tone,
}: {
  title: string;
  value: string;
  percentage: string;
  tone: "emerald" | "amber" | "red";
}) {

  const classes = {
    emerald:
      "border-emerald-300/10 bg-emerald-300/[0.025]",
    amber:
      "border-amber-300/10 bg-amber-300/[0.025]",
    red:
      "border-red-300/10 bg-red-300/[0.025]",
  };


  const valueClasses = {
    emerald:
      "text-emerald-200",
    amber:
      "text-amber-200",
    red:
      "text-red-200",
  };


  return (

    <div
      className={`rounded-3xl border p-5 ${classes[tone]}`}
    >

      <p className="text-sm font-medium text-white/70">
        {title}
      </p>


      <div className="mt-3 flex items-end justify-between gap-4">

        <p
          className={`text-3xl font-semibold ${valueClasses[tone]}`}
        >
          {value}
        </p>


        <p className="text-sm text-white/35">
          {percentage}
        </p>

      </div>

    </div>
  );
}


/* ============================================================
   AMBIENT BACKGROUND
   ============================================================ */

function AmbientBackground() {

  return (

    <div
      className="pointer-events-none fixed inset-0 overflow-hidden"
      aria-hidden="true"
    >

      <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_12%,rgba(34,211,238,0.06),transparent_27%),radial-gradient(circle_at_88%_30%,rgba(139,92,246,0.065),transparent_30%),radial-gradient(circle_at_55%_100%,rgba(59,130,246,0.035),transparent_28%)]" />


      <div
        className="absolute inset-0 opacity-[0.035]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(103,232,249,.18) 1px, transparent 1px), linear-gradient(90deg, rgba(103,232,249,.18) 1px, transparent 1px)",
          backgroundSize:
            "72px 72px",
        }}
      />


      <motion.div
        className="absolute -left-44 top-24 h-[30rem] w-[30rem] rounded-full bg-cyan-400/10 blur-3xl"
        animate={{
          x: [
            0,
            60,
            0,
          ],
          y: [
            0,
            35,
            0,
          ],
          scale: [
            1,
            1.08,
            1,
          ],
        }}
        transition={{
          duration: 13,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />


      <motion.div
        className="absolute right-[-150px] top-[35%] h-[34rem] w-[34rem] rounded-full bg-violet-500/10 blur-3xl"
        animate={{
          x: [
            0,
            -55,
            0,
          ],
          y: [
            0,
            45,
            0,
          ],
          scale: [
            1,
            1.1,
            1,
          ],
        }}
        transition={{
          duration: 16,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />


      <div className="absolute left-[8%] top-[38%] hidden h-56 w-56 lg:block">

        <motion.div
          className="absolute inset-0 rounded-full border border-cyan-300/[0.055]"
          animate={{
            scale: [
              0.82,
              1.05,
              0.82,
            ],
            opacity: [
              0.15,
              0.45,
              0.15,
            ],
          }}
          transition={{
            duration: 9,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />


        <motion.div
          className="absolute inset-8 rounded-full border border-cyan-300/[0.035]"
          animate={{
            rotate: 360,
          }}
          transition={{
            duration: 30,
            repeat: Infinity,
            ease: "linear",
          }}
        />

      </div>


      <div className="absolute right-[8%] top-[54%] hidden h-64 w-64 lg:block">

        <motion.div
          className="absolute inset-0 rounded-full border border-violet-300/[0.05]"
          animate={{
            scale: [
              0.8,
              1.04,
              0.8,
            ],
            opacity: [
              0.12,
              0.4,
              0.12,
            ],
          }}
          transition={{
            duration: 10,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />


        <motion.div
          className="absolute inset-9 rounded-full border border-violet-300/[0.03]"
          animate={{
            rotate: -360,
          }}
          transition={{
            duration: 32,
            repeat: Infinity,
            ease: "linear",
          }}
        />

      </div>


      <motion.div
        className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-cyan-300/10 to-transparent"
        animate={{
          top: [
            "12%",
            "88%",
            "12%",
          ],
        }}
        transition={{
          duration: 22,
          repeat: Infinity,
          ease: "linear",
        }}
      />

    </div>
  );
}