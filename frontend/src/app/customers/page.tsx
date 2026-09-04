"use client";

import {
  ArrowLeft,
  ArrowRight,
  Fingerprint,
  Search,
  Sparkles,
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

const FORENSIC_POINTS = [
  ["8%", "18%"],
  ["17%", "72%"],
  ["29%", "29%"],
  ["43%", "16%"],
  ["56%", "78%"],
  ["68%", "34%"],
  ["79%", "69%"],
  ["91%", "22%"],
];


// ============================================================
// HELPERS
// ============================================================

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
    .replaceAll(
      "_",
      " "
    )
    .toLowerCase()
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase()
    );
}


function getInitials(
  customer: Customer
) {
  const first =
    customer.first_name ??
    "";

  const last =
    customer.last_name ??
    "";

  const initials =
    `${first.charAt(0)}${last.charAt(0)}`;

  return (
    initials ||
    "CU"
  ).toUpperCase();
}


// ============================================================
// PAGE
// ============================================================

export default function CustomersPage() {

  const [
    customers,
    setCustomers,
  ] = useState<Customer[]>([]);

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
    segment,
    setSegment,
  ] = useState("ALL");

  const [
    page,
    setPage,
  ] = useState(1);


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


    void loadCustomers();


    return () => {
      active = false;
    };

  }, []);


  // ==========================================================
  // FILTERED CUSTOMERS
  // ==========================================================

  const filteredCustomers =
    useMemo(() => {

      const query =
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


          const country =
            (
              customer.country ??
              ""
            )
              .toLowerCase();


          const customerId =
            customer.customer_id
              .toLowerCase();


          const matchesSearch =
            !query ||
            customerId.includes(
              query
            ) ||
            fullName.includes(
              query
            ) ||
            country.includes(
              query
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
      safePage -
      1
    ) *
    PAGE_SIZE;


  const visibleCustomers =
    filteredCustomers.slice(
      startIndex,
      startIndex +
        PAGE_SIZE
    );


  // ==========================================================
  // SEGMENT COUNTS
  // ==========================================================

  const segmentCounts =
    useMemo(() => {

      const counts:
        Record<
          string,
          number
        > = {};


      for (
        const customer of
        customers
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
  // PAGE
  // ==========================================================

  return (

    <main className="relative min-h-screen overflow-hidden bg-[#07111f] text-white">


      {/* ======================================================
          FORENSIC BACKGROUND
          ====================================================== */}

      <div
        className="pointer-events-none fixed inset-0 overflow-hidden"
        aria-hidden="true"
      >

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_15%_10%,rgba(34,211,238,0.055),transparent_28%),radial-gradient(circle_at_90%_40%,rgba(139,92,246,0.065),transparent_32%)]" />


        <div
          className="absolute inset-0 opacity-[0.035]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(103,232,249,.2) 1px, transparent 1px), linear-gradient(90deg, rgba(103,232,249,.2) 1px, transparent 1px)",
            backgroundSize:
              "70px 70px",
            maskImage:
              "radial-gradient(circle at center, black, transparent 80%)",
            WebkitMaskImage:
              "radial-gradient(circle at center, black, transparent 80%)",
          }}
        />


        <motion.div
          className="absolute -left-48 top-40 h-[32rem] w-[32rem] rounded-full bg-cyan-400/[0.06] blur-3xl"
          animate={{
            x: [0, 70, 0],
            y: [0, 35, 0],
            scale: [1, 1.12, 1],
          }}
          transition={{
            duration: 14,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />


        <motion.div
          className="absolute -right-40 top-[35%] h-[34rem] w-[34rem] rounded-full bg-violet-500/[0.065] blur-3xl"
          animate={{
            x: [0, -60, 0],
            y: [0, 50, 0],
            scale: [1, 1.1, 1],
          }}
          transition={{
            duration: 16,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />


        {FORENSIC_POINTS.map(
          (
            [left, top],
            index
          ) => (

            <motion.span
              key={index}
              className="absolute h-1.5 w-1.5 rounded-full bg-cyan-300/25 shadow-[0_0_12px_rgba(103,232,249,0.25)]"
              style={{
                left,
                top,
              }}
              animate={{
                y: [
                  0,
                  -10,
                  0,
                ],

                opacity: [
                  0.1,
                  0.5,
                  0.1,
                ],
              }}
              transition={{
                duration:
                  5 +
                  index *
                    0.35,

                delay:
                  index *
                  0.4,

                repeat:
                  Infinity,

                ease:
                  "easeInOut",
              }}
            />

          )
        )}

      </div>


      {/* ======================================================
          TOP BAR
          ====================================================== */}

      <div className="relative z-10 border-b border-white/10 bg-[#071321]/75 backdrop-blur-xl">

        <div className="mx-auto flex max-w-7xl items-center justify-between px-6 py-4">

          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-white/45 transition hover:text-white"
          >

            <ArrowLeft className="h-4 w-4" />

            Overview

          </Link>


          <div className="flex items-center gap-2 rounded-full border border-cyan-300/10 bg-cyan-300/[0.04] px-3 py-2 text-[11px] text-cyan-200/70">

            <Fingerprint className="h-3.5 w-3.5" />

            Customer intelligence

          </div>

        </div>

      </div>


      {/* ======================================================
          CONTENT
          ====================================================== */}

      <section className="relative z-10 mx-auto max-w-7xl px-6 py-12">


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

          <div className="flex flex-col gap-7 lg:flex-row lg:items-end lg:justify-between">

            <div>

              <div className="flex items-center gap-2 text-sm text-cyan-300/70">

                <Sparkles className="h-4 w-4" />

                Customer intelligence

              </div>


              <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">

                Know every customer.

              </h1>


              <p className="mt-4 max-w-2xl text-base leading-7 text-white/40">

                Explore validated customer profiles,
                behavioral segments and individual
                intelligence signals.

              </p>

            </div>


            <div className="rounded-[1.5rem] border border-white/10 bg-white/[0.035] px-6 py-5 backdrop-blur-xl">

              <div className="flex items-center gap-2 text-xs text-white/30">

                <Users className="h-4 w-4 text-cyan-300/70" />

                Customer population

              </div>


              <p className="mt-2 text-3xl font-semibold">

                {customers.length.toLocaleString()}

              </p>


              <p className="mt-1 text-xs text-emerald-300/60">
                Validated analytical profiles
              </p>

            </div>

          </div>

        </motion.div>


        {/* ====================================================
            SEGMENT CARDS
            ==================================================== */}

        <div className="mt-8 grid gap-3 sm:grid-cols-2 lg:grid-cols-4 xl:grid-cols-7">

          {SEGMENTS.map(
            (
              item,
              index
            ) => {

              const count =
                item ===
                "ALL"
                  ? customers.length
                  : segmentCounts[
                      item
                    ] ?? 0;


              const active =
                segment ===
                item;


              return (

                <motion.button
                  key={item}
                  type="button"

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
                      index *
                      0.04,
                  }}

                  whileHover={{
                    y: -3,
                  }}

                  whileTap={{
                    scale: 0.98,
                  }}

                  onClick={() => {
                    setSegment(item);
                    setPage(1);
                  }}

                  className={`relative overflow-hidden rounded-2xl border p-4 text-left transition ${
                    active
                      ? "border-cyan-300/25 bg-cyan-300/[0.08] shadow-[0_10px_30px_rgba(34,211,238,0.05)]"
                      : "border-white/10 bg-white/[0.03] hover:border-white/15 hover:bg-white/[0.045]"
                  }`}
                >

                  {active && (

                    <motion.div
                      layoutId="customer-segment-active"
                      className="absolute inset-x-0 bottom-0 h-px bg-gradient-to-r from-transparent via-cyan-300 to-transparent"
                    />

                  )}


                  <p className="text-[10px] uppercase tracking-wider text-white/30">

                    {item.replace(
                      "_",
                      " "
                    )}

                  </p>


                  <p className="mt-2 text-xl font-semibold">

                    {count.toLocaleString()}

                  </p>

                </motion.button>

              );

            }
          )}

        </div>


        {/* ====================================================
            FILTER BAR
            ==================================================== */}

        <motion.div
          initial={{
            opacity: 0,
            y: 14,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            delay: 0.28,
          }}
          className="mt-7 rounded-[1.8rem] border border-white/10 bg-white/[0.035] p-4 backdrop-blur-xl"
        >

          <div className="flex flex-col gap-4 xl:flex-row xl:items-center">

            <div className="relative flex-1">

              <Search className="pointer-events-none absolute left-4 top-1/2 h-4 w-4 -translate-y-1/2 text-white/25" />


              <input
                value={search}
                onChange={(event) => {
                  setSearch(
                    event.target.value
                  );
                  setPage(1);
                }}
                placeholder="Search customer ID, name or country..."
                className="w-full rounded-2xl border border-white/10 bg-[#07111f]/60 py-3.5 pl-11 pr-4 text-sm text-white outline-none placeholder:text-white/20 transition focus:border-cyan-300/25 focus:ring-4 focus:ring-cyan-300/[0.04]"
              />

            </div>


            <div className="flex items-center gap-2 overflow-x-auto pb-1 xl:pb-0">

              {SEGMENTS.map(
                (
                  item
                ) => (

                  <button
                    key={item}
                    type="button"
                    onClick={() => {
                      setSegment(item);
                      setPage(1);
                    }}
                    className={`whitespace-nowrap rounded-xl border px-3.5 py-2.5 text-xs font-medium transition ${
                      segment ===
                      item
                        ? "border-cyan-300/20 bg-cyan-300 text-[#07111f]"
                        : "border-transparent bg-white/[0.035] text-white/40 hover:bg-white/[0.06] hover:text-white"
                    }`}
                  >

                    {item}

                  </button>

                )
              )}

            </div>

          </div>


          <div className="mt-3 flex items-center justify-between text-[11px] text-white/25">

            <span>

              {filteredCustomers.length.toLocaleString()}
              {" "}
              matching customers

            </span>


            {(search ||
              segment !==
                "ALL") && (

              <button
                type="button"
                onClick={() => {
                  setSearch("");
                  setSegment("ALL");
                  setPage(1);
                }}
                className="text-cyan-300/60 transition hover:text-cyan-200"
              >

                Clear filters

              </button>

            )}

          </div>

        </motion.div>


        {/* ====================================================
            ERROR
            ==================================================== */}

        {error && (

          <motion.div
            initial={{
              opacity: 0,
              y: 10,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            className="mt-5 rounded-2xl border border-red-300/15 bg-red-300/[0.05] px-5 py-4 text-sm text-red-200/80"
          >

            {error}

          </motion.div>

        )}


        {/* ====================================================
            CUSTOMER GRID
            ==================================================== */}

        {loading ? (

          <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">

            {Array.from(
              {
                length: 6,
              }
            ).map(
              (_, index) => (

                <motion.div
                  key={index}
                  initial={{
                    opacity: 0,
                  }}
                  animate={{
                    opacity: 1,
                  }}
                  className="h-[275px] animate-pulse rounded-[1.8rem] border border-white/10 bg-white/[0.035]"
                />

              )
            )}

          </div>

        ) : visibleCustomers.length === 0 ? (

          <motion.div
            initial={{
              opacity: 0,
              y: 15,
            }}
            animate={{
              opacity: 1,
              y: 0,
            }}
            className="mt-8 rounded-[2rem] border border-dashed border-white/10 bg-white/[0.025] px-6 py-16 text-center"
          >

            <div className="mx-auto flex h-14 w-14 items-center justify-center rounded-2xl bg-white/5">

              <Search className="h-6 w-6 text-white/25" />

            </div>


            <h2 className="mt-5 text-xl font-semibold">
              No customers found
            </h2>


            <p className="mt-2 text-sm text-white/35">
              Try a different name, ID, country or segment.
            </p>


            <button
              type="button"
              onClick={() => {
                setSearch("");
                setSegment("ALL");
                setPage(1);
              }}
              className="mt-6 rounded-xl border border-cyan-300/15 bg-cyan-300/5 px-4 py-2.5 text-xs text-cyan-200/70 transition hover:bg-cyan-300/10"
            >

              Reset filters

            </button>

          </motion.div>

        ) : (

          <>

            <div className="mt-8 grid gap-4 md:grid-cols-2 xl:grid-cols-3">

              {visibleCustomers.map(
                (
                  customer,
                  index
                ) => {

                  const customerSegment =
                    customer.customer_segment ??
                    "OTHER";


                  const fullName =
                    `${customer.first_name ?? ""} ${
                      customer.last_name ?? ""
                    }`
                      .trim() ||
                    "Customer";


                  return (

                    <Link
                      href={`/customers/${customer.customer_id}`}
                      key={
                        customer.customer_id
                      }
                    >

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
                          delay:
                            (index %
                              6) *
                            0.045,
                          duration:
                            0.42,
                        }}

                        whileHover={{
                          y: -6,
                          scale: 1.01,
                        }}

                        className="group relative h-full overflow-hidden rounded-[1.8rem] border border-white/10 bg-white/[0.04] p-5 shadow-[0_14px_35px_rgba(0,0,0,0.08)] backdrop-blur-xl transition hover:border-cyan-300/15"
                      >

                        {/* CARD GLOW */}

                        <div className="pointer-events-none absolute -right-16 -top-16 h-40 w-40 rounded-full bg-cyan-300/[0.04] blur-3xl transition duration-500 group-hover:bg-cyan-300/[0.09]" />


                        {/* CARD SHEEN */}

                        <motion.div
                          className="pointer-events-none absolute inset-y-0 left-[-45%] w-[24%] bg-gradient-to-r from-transparent via-white/[0.045] to-transparent blur-sm"
                          animate={{
                            x: [
                              "-110%",
                              "570%",
                            ],
                          }}
                          transition={{
                            duration:
                              6,
                            repeat:
                              Infinity,
                            repeatDelay:
                              5 +
                              index,
                            ease:
                              "easeInOut",
                          }}
                        />


                        <div className="relative">

                          {/* TOP */}

                          <div className="flex items-start justify-between gap-3">

                            <div className="flex min-w-0 items-center gap-3">

                              <motion.div
                                whileHover={{
                                  rotate:
                                    5,
                                  scale:
                                    1.05,
                                }}
                                className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl border border-cyan-300/10 bg-cyan-300/[0.06] text-sm font-semibold text-cyan-200"
                              >

                                {getInitials(
                                  customer
                                )}

                              </motion.div>


                              <div className="min-w-0">

                                <p className="truncate font-semibold text-white/90">
                                  {fullName}
                                </p>

                                <p className="mt-1 truncate font-mono text-[10px] text-white/30">
                                  {
                                    customer.customer_id
                                  }
                                </p>

                              </div>

                            </div>


                            <span
                              className={`shrink-0 rounded-full border px-2.5 py-1 text-[9px] font-medium uppercase ${segmentClass(
                                customerSegment
                              )}`}
                            >

                              {formatSegment(
                                customerSegment
                              )}

                            </span>

                          </div>


                          {/* DETAILS */}

                          <div className="mt-6 grid grid-cols-2 gap-3">

                            <div className="rounded-2xl border border-white/5 bg-black/10 p-3.5">

                              <p className="text-[10px] uppercase tracking-wider text-white/25">
                                Country
                              </p>

                              <p className="mt-1.5 truncate text-sm text-white/70">
                                {
                                  customer.country ??
                                  "Unknown"
                                }
                              </p>

                            </div>


                            <div className="rounded-2xl border border-white/5 bg-black/10 p-3.5">

                              <p className="text-[10px] uppercase tracking-wider text-white/25">
                                Segment
                              </p>

                              <p className="mt-1.5 truncate text-sm text-white/70">
                                {
                                  formatSegment(
                                    customerSegment
                                  )
                                }
                              </p>

                            </div>

                          </div>


                          {/* FOOTER */}

                          <div className="mt-5 flex items-center justify-between rounded-2xl border border-white/5 bg-white/[0.025] px-4 py-3 transition group-hover:border-cyan-300/10 group-hover:bg-cyan-300/[0.025]">

                            <div className="flex items-center gap-2">

                              <Fingerprint className="h-3.5 w-3.5 text-cyan-300/60" />

                              <span className="text-[11px] text-white/35">
                                Open intelligence profile
                              </span>

                            </div>


                            <ArrowRight className="h-4 w-4 text-white/20 transition group-hover:translate-x-1 group-hover:text-cyan-200" />

                          </div>

                        </div>

                      </motion.div>

                    </Link>

                  );

                }
              )}

            </div>


            {/* ==================================================
                PAGINATION
                ================================================== */}

            <div className="mt-8 flex flex-col gap-4 border-t border-white/5 pt-6 sm:flex-row sm:items-center sm:justify-between">

              <div>

                <p className="text-xs text-white/30">

                  Showing{" "}

                  <span className="text-white/60">
                    {filteredCustomers.length ===
                    0
                      ? 0
                      : startIndex +
                        1}
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
                    {
                      filteredCustomers.length
                    }
                  </span>

                </p>


                <p className="mt-1 text-[10px] text-white/20">
                  Page {safePage} of {totalPages}
                </p>

              </div>


              <div className="flex items-center gap-2">

                <motion.button
                  type="button"
                  disabled={
                    safePage <=
                    1
                  }
                  onClick={() =>
                    setPage(
                      (
                        current
                      ) =>
                        Math.max(
                          1,
                          current -
                            1
                        )
                    )
                  }
                  whileTap={{
                    scale:
                      0.95,
                  }}
                  className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-white/50 transition hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-25"
                >

                  <ArrowLeft className="h-4 w-4" />

                </motion.button>


                <div className="flex h-10 items-center rounded-xl border border-white/10 bg-white/[0.03] px-4 text-xs text-white/55">

                  {safePage}
                  {" / "}
                  {totalPages}

                </div>


                <motion.button
                  type="button"
                  disabled={
                    safePage >=
                    totalPages
                  }
                  onClick={() =>
                    setPage(
                      (
                        current
                      ) =>
                        Math.min(
                          totalPages,
                          current +
                            1
                        )
                    )
                  }
                  whileTap={{
                    scale:
                      0.95,
                  }}
                  className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-white/50 transition hover:bg-white/10 hover:text-white disabled:cursor-not-allowed disabled:opacity-25"
                >

                  <ArrowRight className="h-4 w-4" />

                </motion.button>

              </div>

            </div>

          </>

        )}

      </section>


      {/* ======================================================
          FOOTER
          ====================================================== */}

      <footer className="relative z-10 border-t border-white/10 px-6 py-6">

        <div className="mx-auto flex max-w-7xl flex-col justify-between gap-3 text-xs text-white/25 sm:flex-row">

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