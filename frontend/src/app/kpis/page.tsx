"use client";

import {
  Activity,
  AlertTriangle,
  ArrowLeft,
  BarChart3,
  CheckCircle2,
  CircleDollarSign,
  Database,
  Gauge,
  Info,
  Layers3,
  RefreshCw,
  Search,
  ShieldAlert,
  Target,
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
  getKPIs,
  type KPI,
  type KPIResponse,
} from "@/lib/api";


/* ============================================================
   FILTERS
   ============================================================ */

const STATUS_FILTERS = [
  "ALL",
  "AVAILABLE",
  "PROXY",
  "NOT_SUPPORTED",
];


/* ============================================================
   FORMAT KPI NAME
   ============================================================ */

function formatKPIName(
  name: string
): string {

  return name
    .toLowerCase()
    .split("_")
    .map(
      (word) =>
        word.charAt(0).toUpperCase() +
        word.slice(1)
    )
    .join(" ");
}


/* ============================================================
   FORMAT VALUE
   ============================================================ */

function formatKPIValue(
  kpi: KPI
): string {

  if (
    kpi.value === null ||
    kpi.value === undefined
  ) {
    return "—";
  }

  const unit =
    kpi.unit.toLowerCase();

  if (
    unit === "rate"
  ) {

    return `${(
      kpi.value * 100
    ).toFixed(2)}%`;
  }

  if (
    unit ===
    "currency_units"
  ) {

    return kpi.value.toLocaleString(
      undefined,
      {
        maximumFractionDigits: 2,
      }
    );
  }

  if (
    unit.includes(
      "currency_units/customer"
    ) ||
    unit.includes(
      "currency_units/booking"
    )
  ) {

    return kpi.value.toLocaleString(
      undefined,
      {
        maximumFractionDigits: 2,
      }
    );
  }

  if (
    unit ===
      "customers" ||
    unit ===
      "bookings" ||
    unit ===
      "attempts" ||
    unit ===
      "events"
  ) {

    return kpi.value.toLocaleString(
      undefined,
      {
        maximumFractionDigits: 0,
      }
    );
  }

  return kpi.value.toLocaleString(
    undefined,
    {
      maximumFractionDigits: 4,
    }
  );
}


/* ============================================================
   STATUS STYLE
   ============================================================ */

function statusClass(
  status: string
): string {

  switch (
    status.toUpperCase()
  ) {

    case "AVAILABLE":

      return "border-emerald-300/20 bg-emerald-300/10 text-emerald-200";

    case "PROXY":

      return "border-amber-300/20 bg-amber-300/10 text-amber-200";

    case "NOT_SUPPORTED":

      return "border-red-300/20 bg-red-300/10 text-red-200";

    default:

      return "border-white/10 bg-white/5 text-white/50";
  }
}


/* ============================================================
   STATUS ICON
   ============================================================ */

function StatusIcon({
  status,
}: {
  status: string;
}) {

  switch (
    status.toUpperCase()
  ) {

    case "AVAILABLE":

      return (
        <CheckCircle2 className="h-4 w-4 text-emerald-300" />
      );

    case "PROXY":

      return (
        <AlertTriangle className="h-4 w-4 text-amber-300" />
      );

    case "NOT_SUPPORTED":

      return (
        <XCircle className="h-4 w-4 text-red-300" />
      );

    default:

      return (
        <Info className="h-4 w-4 text-white/40" />
      );
  }
}


/* ============================================================
   KPI CATEGORY ICON
   ============================================================ */

function KPIIcon({
  name,
}: {
  name: string;
}) {

  if (
    name.includes("REVENUE") ||
    name.includes("BOOKING_VALUE")
  ) {

    return (
      <CircleDollarSign className="h-5 w-5 text-cyan-300" />
    );
  }

  if (
    name.includes("PAYMENT")
  ) {

    return (
      <ShieldAlert className="h-5 w-5 text-cyan-300" />
    );
  }

  if (
    name.includes("RATE")
  ) {

    return (
      <Gauge className="h-5 w-5 text-cyan-300" />
    );
  }

  if (
    name.includes("CUSTOMER")
  ) {

    return (
      <Target className="h-5 w-5 text-cyan-300" />
    );
  }

  if (
    name.includes("JOURNEY") ||
    name.includes("FRICTION")
  ) {

    return (
      <Activity className="h-5 w-5 text-cyan-300" />
    );
  }

  return (
    <BarChart3 className="h-5 w-5 text-cyan-300" />
  );
}


/* ============================================================
   KPI CARD
   ============================================================ */

function KPICard({
  kpi,
  index,
  onSelect,
}: {
  kpi: KPI;
  index: number;
  onSelect: () => void;
}) {

  const supported =
    kpi.status !==
    "NOT_SUPPORTED";


  return (

    <motion.button
      type="button"
      onClick={onSelect}
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
          index * 0.035,
        duration: 0.45,
      }}
      whileHover={{
        y: -5,
      }}
      className="group text-left"
    >

      <div className="h-full rounded-[1.8rem] border border-white/10 bg-white/[0.04] p-5 backdrop-blur-xl transition group-hover:border-cyan-300/15 group-hover:bg-white/[0.055]">

        <div className="flex items-start justify-between gap-3">

          <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/5">

            <KPIIcon
              name={
                kpi.kpi_name
              }
            />

          </div>


          <div
            className={`flex items-center gap-1.5 rounded-full border px-2.5 py-1 text-[9px] font-medium uppercase ${statusClass(
              kpi.status
            )}`}
          >

            <StatusIcon
              status={
                kpi.status
              }
            />

            {kpi.status.replace(
              "_",
              " "
            )}

          </div>

        </div>


        <p className="mt-5 min-h-[40px] text-sm font-medium leading-5 text-white/75">

          {formatKPIName(
            kpi.kpi_name
          )}

        </p>


        <p
          className={`mt-4 text-3xl font-semibold ${
            !supported
              ? "text-white/25"
              : "text-white"
          }`}
        >

          {formatKPIValue(
            kpi
          )}

        </p>


        <p className="mt-2 text-[10px] uppercase tracking-wider text-white/25">

          {kpi.unit.replace(
            "_",
            " "
          )}

        </p>


        <p className="mt-4 line-clamp-2 text-xs leading-5 text-white/30">

          {kpi.definition}

        </p>


        <div className="mt-5 flex items-center justify-between text-[10px] text-white/25">

          <span>
            View definition
          </span>

          <ArrowLeft
            className="h-3.5 w-3.5 rotate-180 transition group-hover:translate-x-1"
          />

        </div>

      </div>

    </motion.button>
  );
}


/* ============================================================
   PAGE
   ============================================================ */

export default function KPIsPage() {

  const [
    data,
    setData,
  ] = useState<KPIResponse | null>(
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


  const [
    search,
    setSearch,
  ] = useState("");


  const [
    statusFilter,
    setStatusFilter,
  ] = useState("ALL");


  const [
    selectedKPI,
    setSelectedKPI,
  ] = useState<KPI | null>(
    null
  );


  /* ==========================================================
     LOAD
     ========================================================== */

  const loadKPIs =
    useCallback(
      async () => {

        try {

          setLoading(
            true
          );

          const response =
            await getKPIs();

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
              : "Unable to load KPI intelligence."
          );

        } finally {

          setLoading(
            false
          );
        }

      },
      []
    );


  useEffect(() => {

    // eslint-disable-next-line react-hooks/set-state-in-effect
    void loadKPIs();

  }, [
    loadKPIs,
  ]);


  /* ==========================================================
     FILTERED KPIS
     ========================================================== */

  const filteredKPIs =
    useMemo(() => {

      if (!data) {
        return [];
      }


      const query =
        search
          .trim()
          .toLowerCase();


      return data.kpis.filter(
        (kpi) => {

          const matchesStatus =
            statusFilter === "ALL" ||
            kpi.status ===
              statusFilter;


          const matchesSearch =
            !query ||
            kpi.kpi_name
              .toLowerCase()
              .includes(
                query
              ) ||
            kpi.definition
              .toLowerCase()
              .includes(
                query
              );


          return (
            matchesStatus &&
            matchesSearch
          );
        }
      );

    }, [
      data,
      search,
      statusFilter,
    ]);


  /* ==========================================================
     LOADING
     ========================================================== */

  if (loading) {

    return (

      <main className="relative min-h-screen overflow-hidden bg-[#07111f] text-white">

        <Background />


        <section className="relative z-10 mx-auto max-w-7xl px-6 py-12">

          <div className="h-8 w-56 animate-pulse rounded-xl bg-white/10" />


          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-4">

            {Array.from({
              length: 8,
            }).map(
              (
                _,
                index
              ) => (

                <div
                  key={
                    index
                  }
                  className="h-64 animate-pulse rounded-[1.8rem] bg-white/[0.04]"
                />

              )
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

        <Background />


        <section className="relative z-10 mx-auto max-w-3xl px-6 py-24 text-center">

          <XCircle className="mx-auto h-12 w-12 text-red-300" />


          <h1 className="mt-5 text-3xl font-semibold">

            KPI intelligence unavailable

          </h1>


          <p className="mt-3 text-white/40">

            {error ??
              "Unable to retrieve KPI data."}

          </p>


          <button
            type="button"
            onClick={() =>
              void loadKPIs()
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
     RENDER
     ========================================================== */

  return (

    <main className="relative min-h-screen overflow-hidden bg-[#07111f] text-white">

      <Background />


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

              <div className="flex items-center gap-2 text-cyan-300/70">

                <Activity className="h-4 w-4" />

                Validated business intelligence

              </div>


              <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">

                Every metric.

                <span className="block bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400 bg-clip-text text-transparent">

                  One source of truth.

                </span>

              </h1>


              <p className="mt-4 max-w-3xl text-base leading-7 text-white/45">

                Explore validated analytics metrics,
                their definitions, availability status and
                the boundaries of what the current data
                supports.

              </p>

            </div>


            <button
              type="button"
              onClick={() =>
                void loadKPIs()
              }
              className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-5 py-3 text-sm text-white/60 transition hover:bg-white/10 hover:text-white"
            >

              <RefreshCw className="h-4 w-4" />

              Refresh KPIs

            </button>

          </div>

        </motion.div>


        {/* ====================================================
            SUMMARY
            ==================================================== */}

        <div className="mt-9 grid gap-4 sm:grid-cols-2 lg:grid-cols-4">


          <motion.div
            initial={{
              opacity: 0,
              y: 18,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            className="rounded-[2rem] border border-cyan-300/10 bg-cyan-300/[0.035] p-6"
          >

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-cyan-300/10">

              <Layers3 className="h-5 w-5 text-cyan-300" />

            </div>


            <p className="mt-6 text-xs text-white/35">
              Total metrics
            </p>


            <p className="mt-1 text-4xl font-semibold">
              {data.total_kpis}
            </p>


            <p className="mt-2 text-xs text-cyan-200/60">
              Validated KPI catalog
            </p>

          </motion.div>


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
              delay: 0.07,
            }}
            className="rounded-[2rem] border border-emerald-300/10 bg-emerald-300/[0.035] p-6"
          >

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-emerald-300/10">

              <CheckCircle2 className="h-5 w-5 text-emerald-300" />

            </div>


            <p className="mt-6 text-xs text-white/35">
              Available
            </p>


            <p className="mt-1 text-4xl font-semibold">
              {data.available_kpis}
            </p>


            <p className="mt-2 text-xs text-emerald-200/60">
              Directly supported
            </p>

          </motion.div>


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
              delay: 0.14,
            }}
            className="rounded-[2rem] border border-amber-300/10 bg-amber-300/[0.035] p-6"
          >

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-amber-300/10">

              <AlertTriangle className="h-5 w-5 text-amber-300" />

            </div>


            <p className="mt-6 text-xs text-white/35">
              Proxy
            </p>


            <p className="mt-1 text-4xl font-semibold">
              {data.proxy_kpis}
            </p>


            <p className="mt-2 text-xs text-amber-200/60">
              Explicitly marked proxy
            </p>

          </motion.div>


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
              delay: 0.21,
            }}
            className="rounded-[2rem] border border-red-300/10 bg-red-300/[0.035] p-6"
          >

            <div className="flex h-11 w-11 items-center justify-center rounded-2xl bg-red-300/10">

              <XCircle className="h-5 w-5 text-red-300" />

            </div>


            <p className="mt-6 text-xs text-white/35">
              Not supported
            </p>


            <p className="mt-1 text-4xl font-semibold">
              {data.unsupported_kpis}
            </p>


            <p className="mt-2 text-xs text-red-200/60">
              Current data limitation
            </p>

          </motion.div>

        </div>


        {/* ====================================================
            DATA TRUST BANNER
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
            delay: 0.25,
          }}
          className="mt-5 rounded-[2rem] border border-white/10 bg-white/[0.035] p-6"
        >

          <div className="flex flex-col gap-5 lg:flex-row lg:items-center lg:justify-between">

            <div className="flex items-start gap-4">

              <div className="flex h-11 w-11 shrink-0 items-center justify-center rounded-2xl bg-white/5">

                <Database className="h-5 w-5 text-cyan-300" />

              </div>


              <div>

                <p className="text-sm font-semibold">
                  KPI catalog is source-reconciled
                </p>


                <p className="mt-1 max-w-3xl text-xs leading-6 text-white/35">

                  Available values come directly from the
                  validated KPI source. Proxy and unsupported
                  metrics remain explicitly identified rather
                  than being presented as measured facts.

                </p>

              </div>

            </div>


            <div className="flex shrink-0 items-center gap-2 rounded-full border border-emerald-300/15 bg-emerald-300/5 px-4 py-2 text-xs text-emerald-200/75">

              <CheckCircle2 className="h-4 w-4" />

              Source reconciled

            </div>

          </div>

        </motion.div>


        {/* ====================================================
            SEARCH + FILTER
            ==================================================== */}

        <div className="mt-8 rounded-3xl border border-white/10 bg-white/[0.035] p-4">

          <div className="flex flex-col gap-4 lg:flex-row">

            <div className="relative flex-1">

              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-white/25" />


              <input
                value={
                  search
                }
                onChange={(event) =>
                  setSearch(
                    event.target.value
                  )
                }
                placeholder="Search KPI name or definition..."
                className="w-full rounded-2xl border border-white/10 bg-black/10 py-3 pl-11 pr-4 text-sm text-white outline-none placeholder:text-white/20 focus:border-cyan-300/30"
              />

            </div>


            <div className="flex items-center gap-2 overflow-x-auto">

              {STATUS_FILTERS.map(
                (
                  filter
                ) => (

                  <button
                    key={
                      filter
                    }
                    type="button"
                    onClick={() =>
                      setStatusFilter(
                        filter
                      )
                    }
                    className={`whitespace-nowrap rounded-xl px-4 py-2.5 text-xs transition ${
                      statusFilter ===
                      filter
                        ? "bg-cyan-300 text-[#07111f]"
                        : "bg-white/5 text-white/40 hover:text-white"
                    }`}
                  >

                    {filter.replace(
                      "_",
                      " "
                    )}

                  </button>

                )
              )}

            </div>

          </div>

        </div>


        {/* ====================================================
            RESULTS
            ==================================================== */}

        <div className="mt-8">

          <div className="mb-5 flex items-end justify-between">

            <div>

              <p className="text-sm text-cyan-300/70">
                KPI catalog
              </p>


              <h2 className="mt-1 text-2xl font-semibold">
                {filteredKPIs.length} metrics
              </h2>

            </div>


            <p className="hidden text-xs text-white/25 sm:block">
              Click any metric for details
            </p>

          </div>


          {filteredKPIs.length >
          0 ? (

            <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-3">

              {filteredKPIs.map(
                (
                  kpi,
                  index
                ) => (

                  <KPICard
                    key={
                      kpi.kpi_name
                    }
                    kpi={
                      kpi
                    }
                    index={
                      index
                    }
                    onSelect={() =>
                      setSelectedKPI(
                        kpi
                      )
                    }
                  />

                )
              )}

            </div>

          ) : (

            <div className="rounded-[2rem] border border-white/10 bg-white/[0.035] p-14 text-center">

              <Search className="mx-auto h-8 w-8 text-white/20" />


              <p className="mt-4 text-lg font-medium">
                No metrics found
              </p>


              <p className="mt-2 text-sm text-white/35">
                Try a different search or status filter.
              </p>

            </div>

          )}

        </div>


        {/* ====================================================
            SELECTED KPI
            ==================================================== */}

        {selectedKPI && (

          <motion.div
            initial={{
              opacity: 0,
              y: 20,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            className="mt-8 rounded-[2rem] border border-cyan-300/10 bg-cyan-300/[0.025] p-7"
          >

            <div className="flex flex-col gap-5 sm:flex-row sm:items-start sm:justify-between">

              <div>

                <div className="flex flex-wrap items-center gap-3">

                  <p className="text-sm text-cyan-300/70">
                    Metric definition
                  </p>


                  <span
                    className={`rounded-full border px-3 py-1 text-[10px] font-medium uppercase ${statusClass(
                      selectedKPI.status
                    )}`}
                  >

                    {selectedKPI.status.replace(
                      "_",
                      " "
                    )}

                  </span>

                </div>


                <h2 className="mt-2 text-2xl font-semibold">
                  {formatKPIName(
                    selectedKPI.kpi_name
                  )}
                </h2>

              </div>


              <button
                type="button"
                onClick={() =>
                  setSelectedKPI(
                    null
                  )
                }
                className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs text-white/50 transition hover:bg-white/10 hover:text-white"
              >

                Close

              </button>

            </div>


            <div className="mt-7 grid gap-4 lg:grid-cols-3">

              <div className="rounded-2xl border border-white/5 bg-black/10 p-5">

                <p className="text-xs text-white/30">
                  Current value
                </p>


                <p className="mt-2 text-3xl font-semibold">
                  {formatKPIValue(
                    selectedKPI
                  )}
                </p>

              </div>


              <div className="rounded-2xl border border-white/5 bg-black/10 p-5">

                <p className="text-xs text-white/30">
                  Unit
                </p>


                <p className="mt-2 text-lg font-medium">
                  {selectedKPI.unit}
                </p>

              </div>


              <div className="rounded-2xl border border-white/5 bg-black/10 p-5">

                <p className="text-xs text-white/30">
                  Status
                </p>


                <div className="mt-2 flex items-center gap-2">

                  <StatusIcon
                    status={
                      selectedKPI.status
                    }
                  />


                  <span className="text-lg font-medium">
                    {selectedKPI.status.replace(
                      "_",
                      " "
                    )}
                  </span>

                </div>

              </div>

            </div>


            <div className="mt-5 rounded-2xl border border-cyan-300/10 bg-cyan-300/[0.025] p-5">

              <div className="flex items-center gap-2 text-sm text-cyan-200/80">

                <Info className="h-4 w-4" />

                Definition

              </div>


              <p className="mt-3 max-w-4xl text-sm leading-7 text-white/50">

                {
                  selectedKPI.definition
                }

              </p>

            </div>


            {selectedKPI.status ===
              "PROXY" && (

              <div className="mt-4 rounded-2xl border border-amber-300/10 bg-amber-300/[0.025] p-5">

                <p className="text-sm font-medium text-amber-200">
                  Proxy metric
                </p>


                <p className="mt-2 text-sm leading-6 text-white/40">

                  This metric is intentionally exposed
                  as a proxy and should not be interpreted
                  as a directly measured retention metric.

                </p>

              </div>
            )}


            {selectedKPI.status ===
              "NOT_SUPPORTED" && (

              <div className="mt-4 rounded-2xl border border-red-300/10 bg-red-300/[0.025] p-5">

                <p className="text-sm font-medium text-red-200">
                  Current data limitation
                </p>


                <p className="mt-2 text-sm leading-6 text-white/40">

                  The current analytics foundation does not
                  provide the required complaint data for
                  this metric.

                </p>

              </div>
            )}

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
            Validated KPI intelligence
          </span>

        </div>

      </footer>

    </main>
  );
}


/* ============================================================
   BACKGROUND
   ============================================================ */

function Background() {

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
        className="absolute -left-44 top-20 h-[30rem] w-[30rem] rounded-full bg-cyan-400/10 blur-3xl"
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
          duration: 12,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />


      <motion.div
        className="absolute right-[-140px] top-1/4 h-[34rem] w-[34rem] rounded-full bg-violet-500/10 blur-3xl"
        animate={{
          x: [
            0,
            -50,
            0,
          ],
          y: [
            0,
            50,
            0,
          ],
          scale: [
            1,
            1.1,
            1,
          ],
        }}
        transition={{
          duration: 15,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />


      <div className="absolute left-[8%] top-[35%] hidden h-64 w-64 lg:block">

        <motion.div
          className="absolute inset-0 rounded-full border border-cyan-300/[0.06]"
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
          className="absolute inset-8 rounded-full border border-cyan-300/[0.04]"
          animate={{
            rotate: 360,
          }}
          transition={{
            duration: 30,
            repeat: Infinity,
            ease: "linear",
          }}
        />


        <span className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-300/40 shadow-[0_0_16px_rgba(103,232,249,0.35)]" />

      </div>


      <div className="absolute right-[7%] top-[52%] hidden h-72 w-72 lg:block">

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
          className="absolute inset-9 rounded-full border border-violet-300/[0.035]"
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

    </div>
  );
}