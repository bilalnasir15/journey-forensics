"use client";

import {
  ArrowLeft,
  ArrowRight,
  Search,
  Shield,
  Sparkles,
  TrendingUp,
  Users,
} from "lucide-react";

import {
  motion,
} from "motion/react";

import Link from "next/link";

import {
  useEffect,
  useMemo,
  useState,
} from "react";

import {
  getAllCustomers,
  type Customer,
} from "@/lib/api";


// ============================================================
// CONSTANTS
// ============================================================

const PAGE_SIZE = 12;


const SEGMENTS = [
  "ALL",
  "VIP",
  "LOYAL",
  "AT_RISK",
  "DORMANT",
  "NEW",
  "OTHER",
];


// ============================================================
// SEGMENT STYLE
// ============================================================

function segmentClass(
  segment: string
) {

  switch (segment) {

    case "VIP":
      return "border-amber-300/20 bg-amber-300/10 text-amber-200";

    case "LOYAL":
      return "border-emerald-300/20 bg-emerald-300/10 text-emerald-200";

    case "AT_RISK":
      return "border-red-300/20 bg-red-300/10 text-red-200";

    case "DORMANT":
      return "border-slate-300/20 bg-slate-300/10 text-slate-300";

    case "NEW":
      return "border-cyan-300/20 bg-cyan-300/10 text-cyan-200";

    default:
      return "border-white/10 bg-white/5 text-white/50";
  }
}


// ============================================================
// PAGE
// ============================================================

export default function CustomersPage() {

  const [
    customers,
    setCustomers,
  ] = useState<Customer[]>([]);


  const [loading, setLoading] =
    useState(true);


  const [error, setError] =
    useState<string | null>(
      null
    );


  const [search, setSearch] =
    useState("");


  const [segment, setSegment] =
    useState("ALL");


  const [page, setPage] =
    useState(1);


  // ==========================================================
  // LOAD CUSTOMERS
  // ==========================================================

  useEffect(() => {

    let active = true;

    async function loadCustomers() {

      try {

        setLoading(true);

        const data =
          await getAllCustomers();


        if (!active) {
          return;
        }


        setCustomers(
          data
        );

        setError(
          null
        );

      } catch (err) {

        if (!active) {
          return;
        }

        setError(
          err instanceof Error
            ? err.message
            : "Unable to load customers."
        );

      } finally {

        if (active) {
          setLoading(false);
        }
      }
    }


    loadCustomers();


    return () => {
      active = false;
    };

  }, []);


  // ==========================================================
  // FILTER
  // ==========================================================

  const filteredCustomers =
    useMemo(() => {

      const normalizedSearch =
        search
          .trim()
          .toLowerCase();


      return customers.filter(
        (customer) => {

          const fullName =
            `${customer.first_name ?? ""} ${
              customer.last_name ?? ""
            }`
              .trim()
              .toLowerCase();


          const matchesSearch =
            !normalizedSearch ||
            customer.customer_id
              .toLowerCase()
              .includes(
                normalizedSearch
              ) ||
            fullName.includes(
              normalizedSearch
            ) ||
            (
              customer.country ??
              ""
            )
              .toLowerCase()
              .includes(
                normalizedSearch
              );


          const matchesSegment =
            segment === "ALL" ||
            customer.customer_segment ===
              segment;


          return (
            matchesSearch &&
            matchesSegment
          );
        }
      );

    }, [
      customers,
      search,
      segment,
    ]);


  // ==========================================================
  // PAGINATION
  // ==========================================================

  const totalPages =
    Math.max(
      1,
      Math.ceil(
        filteredCustomers.length /
        PAGE_SIZE
      )
    );


  const safePage =
    Math.min(
      page,
      totalPages
    );


  const startIndex =
    (
      safePage - 1
    ) *
    PAGE_SIZE;


  const visibleCustomers =
    filteredCustomers.slice(
      startIndex,
      startIndex + PAGE_SIZE
    );


  // ==========================================================
  // SEGMENT COUNTS
  // ==========================================================

  const segmentCounts =
    useMemo(() => {

      const counts:
        Record<string, number> = {};


      for (
        const customer
        of customers
      ) {

        const key =
          customer.customer_segment ??
          "OTHER";


        counts[key] =
          (
            counts[key] ??
            0
          ) + 1;
      }


      return counts;

    }, [
      customers,
    ]);


  // ==========================================================
  // RESET PAGE WHEN FILTER CHANGES
  // ==========================================================

  useEffect(() => {

    setPage(1);

  }, [
    search,
    segment,
  ]);


  return (

    <main className="min-h-screen bg-[#07111f] text-white">

      {/* ====================================================
          BACKGROUND
          ==================================================== */}

      <div className="pointer-events-none fixed inset-0 overflow-hidden">

        <motion.div
          className="absolute -left-40 top-20 h-96 w-96 rounded-full bg-cyan-400/10 blur-3xl"
          animate={{
            x: [0, 60, 0],
            y: [0, -30, 0],
          }}
          transition={{
            duration: 11,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

        <motion.div
          className="absolute right-[-160px] top-1/3 h-[30rem] w-[30rem] rounded-full bg-violet-500/10 blur-3xl"
          animate={{
            x: [0, -50, 0],
            y: [0, 40, 0],
          }}
          transition={{
            duration: 13,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />

      </div>


      {/* ====================================================
          NAV
          ==================================================== */}

      <nav className="relative z-10 border-b border-white/10 bg-[#07111f]/75 backdrop-blur-xl">

        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-5">

          <Link
            href="/"
            className="flex items-center gap-3"
          >

            <div className="flex h-10 w-10 items-center justify-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10">

              <Users className="h-5 w-5 text-cyan-300" />

            </div>

            <div>

              <p className="text-sm font-semibold tracking-[0.2em]">
                JOURNEY
              </p>

              <p className="text-xs tracking-[0.3em] text-cyan-300/70">
                FORENSICS
              </p>

            </div>

          </Link>


          <div className="flex items-center gap-2 rounded-full border border-emerald-300/10 bg-emerald-300/5 px-4 py-2 text-xs text-emerald-200/80">

            <span className="h-2 w-2 animate-pulse rounded-full bg-emerald-400" />

            Customer intelligence

          </div>

        </div>

      </nav>


      {/* ====================================================
          CONTENT
          ==================================================== */}

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
            className="mb-6 inline-flex items-center gap-2 text-sm text-white/40 transition hover:text-white"
          >

            <ArrowLeft className="h-4 w-4" />

            Back to overview

          </Link>


          <div className="flex flex-col justify-between gap-6 lg:flex-row lg:items-end">

            <div>

              <div className="mb-3 flex items-center gap-2 text-cyan-300/70">

                <Sparkles className="h-4 w-4" />

                Customer intelligence

              </div>


              <h1 className="text-4xl font-semibold tracking-tight sm:text-5xl">

                Know every customer.

              </h1>


              <p className="mt-4 max-w-2xl text-white/45">

                Explore the validated customer population,
                segment behavior and individual intelligence
                profiles.

              </p>

            </div>


            <div className="rounded-3xl border border-white/10 bg-white/[0.04] px-6 py-5">

              <p className="text-xs text-white/35">
                Total customers
              </p>

              <p className="mt-1 text-3xl font-semibold">
                {customers.length.toLocaleString()}
              </p>

            </div>

          </div>

        </motion.div>


        {/* ==================================================
            SEGMENT SUMMARY
            ================================================== */}

        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">

          {SEGMENTS.map(
            (
              item,
              index
            ) => (

              <motion.button
                key={item}
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
                onClick={() =>
                  setSegment(item)
                }
                className={`rounded-2xl border p-4 text-left transition ${
                  segment === item
                    ? "border-cyan-300/30 bg-cyan-300/10"
                    : "border-white/10 bg-white/[0.03] hover:bg-white/[0.06]"
                }`}
              >

                <p className="text-[11px] text-white/35">
                  {item.replace(
                    "_",
                    " "
                  )}
                </p>

                <p className="mt-2 text-xl font-semibold">

                  {item === "ALL"
                    ? customers.length
                    : segmentCounts[item] ??
                      0}

                </p>

              </motion.button>

            )
          )}

        </div>


        {/* ==================================================
            SEARCH
            ================================================== */}

        <div className="mt-8 rounded-3xl border border-white/10 bg-white/[0.035] p-4 backdrop-blur-xl">

          <div className="flex flex-col gap-4 lg:flex-row">

            <div className="relative flex-1">

              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-white/25" />

              <input
                value={search}
                onChange={(event) =>
                  setSearch(
                    event.target.value
                  )
                }
                placeholder="Search customer ID, name or country..."
                className="w-full rounded-2xl border border-white/10 bg-black/10 py-3 pl-11 pr-4 text-sm text-white outline-none placeholder:text-white/20 focus:border-cyan-300/30"
              />

            </div>


            <div className="flex items-center gap-2 overflow-x-auto">

              {SEGMENTS.map(
                (item) => (

                  <button
                    key={item}
                    onClick={() =>
                      setSegment(item)
                    }
                    className={`whitespace-nowrap rounded-xl px-3 py-2 text-xs transition ${
                      segment === item
                        ? "bg-cyan-300 text-[#07111f]"
                        : "bg-white/5 text-white/40 hover:text-white"
                    }`}
                  >

                    {item}

                  </button>

                )
              )}

            </div>

          </div>

        </div>


        {/* ==================================================
            ERROR
            ================================================== */}

        {error && (

          <div className="mt-5 rounded-2xl border border-red-300/10 bg-red-300/5 px-5 py-4 text-sm text-red-200/80">

            {error}

          </div>

        )}


        {/* ==================================================
            LOADING
            ================================================== */}

        {loading ? (

          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">

            {Array.from(
              { length: 6 }
            ).map(
              (_, index) => (

                <div
                  key={index}
                  className="h-52 animate-pulse rounded-3xl border border-white/10 bg-white/[0.04]"
                />

              )
            )}

          </div>

        ) : (

          <>

            {/* ==================================================
                CUSTOMER CARDS
                ================================================== */}

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">

              {visibleCustomers.map(
                (
                  customer,
                  index
                ) => {

                  const segment =
                    customer.customer_segment ??
                    "OTHER";


                  const initials =
                    `${(
                      customer.first_name ??
                      "?"
                    )
                      .charAt(0)}${
                      (
                        customer.last_name ??
                        "?"
                      )
                        .charAt(0)
                    }`.toUpperCase();


                  return (

                    <motion.div
                      key={customer.customer_id}

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
                          (index %
                            6) *
                          0.04,
                      }}

                      whileHover={{
                        y: -4,
                      }}

                      className="group rounded-3xl border border-white/10 bg-white/[0.04] p-5 backdrop-blur-xl"
                    >

                      <div className="flex items-start justify-between">


                        <div className="flex items-center gap-3">

                          <div className="flex h-12 w-12 items-center justify-center rounded-2xl border border-cyan-300/10 bg-cyan-300/5 text-sm font-semibold text-cyan-200">

                            {initials}

                          </div>


                          <div>

                            <p className="font-semibold">

                              {customer.first_name ||
                              customer.last_name
                                ? `${customer.first_name ?? ""} ${customer.last_name ?? ""}`.trim()
                                : "Customer"}

                            </p>

                            <p className="mt-1 text-xs text-white/35">
                              {customer.customer_id}
                            </p>

                          </div>

                        </div>


                        <span
                          className={`rounded-full border px-2.5 py-1 text-[10px] font-medium ${segmentClass(
                            segment
                          )}`}
                        >

                          {segment}

                        </span>

                      </div>


                      <div className="mt-6 grid grid-cols-2 gap-3">

                        <div className="rounded-2xl bg-white/[0.035] p-3">

                          <p className="text-[10px] text-white/30">
                            Country
                          </p>

                          <p className="mt-1 truncate text-sm text-white/75">
                            {customer.country ??
                              "Unknown"}
                          </p>

                        </div>


                        <div className="rounded-2xl bg-white/[0.035] p-3">

                          <p className="text-[10px] text-white/30">
                            Segment
                          </p>

                          <p className="mt-1 text-sm text-white/75">
                            {segment}
                          </p>

                        </div>

                      </div>


                      <Link
                        href={`/customers/${customer.customer_id}`}
                        className="mt-5 flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.03] px-4 py-3 text-xs text-white/45 transition group-hover:border-cyan-300/20 group-hover:text-cyan-200"
                      >

                        Open intelligence profile

                        <ArrowRight className="h-4 w-4" />

                      </Link>

                    </motion.div>

                  );

                }
              )}

            </div>


            {/* EMPTY STATE */}

            {visibleCustomers.length === 0 && (

              <div className="mt-10 rounded-3xl border border-white/10 bg-white/[0.035] p-14 text-center">

                <Search className="mx-auto h-8 w-8 text-white/20" />

                <p className="mt-4 text-lg font-medium">
                  No customers found
                </p>

                <p className="mt-2 text-sm text-white/35">
                  Try another search or segment.
                </p>

              </div>

            )}


            {/* ==================================================
                PAGINATION
                ================================================== */}

            <div className="mt-8 flex flex-col items-center justify-between gap-4 sm:flex-row">

              <p className="text-xs text-white/30">

                Showing{" "}

                <span className="text-white/60">
                  {filteredCustomers.length === 0
                    ? 0
                    : startIndex + 1}
                </span>

                {" "}–{" "}

                <span className="text-white/60">
                  {Math.min(
                    startIndex +
                      PAGE_SIZE,
                    filteredCustomers.length
                  )}
                </span>

                {" "}of{" "}

                <span className="text-white/60">
                  {filteredCustomers.length}
                </span>

              </p>


              <div className="flex items-center gap-2">

                <button
                  disabled={
                    safePage <= 1
                  }
                  onClick={() =>
                    setPage(
                      (current) =>
                        Math.max(
                          1,
                          current - 1
                        )
                    )
                  }
                  className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-white/50 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-30"
                >

                  <ArrowLeft className="h-4 w-4" />

                </button>


                <div className="rounded-xl border border-white/10 bg-white/5 px-4 py-2 text-xs text-white/60">

                  Page {safePage} / {totalPages}

                </div>


                <button
                  disabled={
                    safePage >=
                    totalPages
                  }
                  onClick={() =>
                    setPage(
                      (current) =>
                        Math.min(
                          totalPages,
                          current + 1
                        )
                    )
                  }
                  className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-white/50 transition hover:bg-white/10 disabled:cursor-not-allowed disabled:opacity-30"
                >

                  <ArrowRight className="h-4 w-4" />

                </button>

              </div>

            </div>

          </>

        )}

      </section>


      {/* ====================================================
          FOOTER
          ==================================================== */}

      <footer className="relative z-10 border-t border-white/10 px-6 py-6">

        <div className="mx-auto flex max-w-7xl justify-between text-xs text-white/25">

          <span>
            Journey Forensics
          </span>

          <span>
            Customer Intelligence
          </span>

        </div>

      </footer>

    </main>
  );
}