"use client";

import {
  Activity,
  BarChart3,
  Database,
  Gauge,
  Layers3,
  Menu,
  UploadCloud,
  Users,
  X,
} from "lucide-react";

import { motion, AnimatePresence } from "motion/react";

import Link from "next/link";

import {
  useEffect,
  useState,
} from "react";

import {
  usePathname,
} from "next/navigation";

import {
  getHealth,
} from "@/lib/api";


// ============================================================
// NAVIGATION ITEMS
// ============================================================

const navigationItems = [
  {
    label: "Overview",
    href: "/",
    icon: Layers3,
  },

  {
    label: "Customers",
    href: "/customers",
    icon: Users,
  },

  {
    label: "Journeys",
    href: "/journeys",
    icon: Activity,
  },

  {
    label: "KPIs",
    href: "/kpis",
    icon: Gauge,
  },

  {
    label: "Quality",
    href: "/quality",
    icon: Database,
  },

  {
    label: "Upload",
    href: "/upload",
    icon: UploadCloud,
  },
];


// ============================================================
// COMPONENT
// ============================================================

export default function AppNavigation() {

  const pathname =
    usePathname();


  const [
    mobileOpen,
    setMobileOpen,
  ] = useState(false);


  const [
    apiOnline,
    setApiOnline,
  ] = useState(false);


  const [
    checkingApi,
    setCheckingApi,
  ] = useState(true);


  // ==========================================================
  // API STATUS
  // ==========================================================

  useEffect(() => {

    let active = true;


    async function checkApi() {

      try {

        setCheckingApi(
          true
        );


        const response =
          await getHealth();


        if (!active) {
          return;
        }


        setApiOnline(
          response.status ===
            "healthy"
        );

      } catch {

        if (!active) {
          return;
        }


        setApiOnline(
          false
        );

      } finally {

        if (active) {

          setCheckingApi(
            false
          );

        }

      }

    }


    checkApi();


    const interval =
      window.setInterval(
        checkApi,
        30000
      );


    return () => {

      active = false;

      window.clearInterval(
        interval
      );

    };

  }, []);


  // ==========================================================
  // CLOSE MOBILE MENU ON ROUTE CHANGE
  // ==========================================================

  useEffect(() => {

    setMobileOpen(
      false
    );

  }, [
    pathname,
  ]);


  // ==========================================================
  // ACTIVE ROUTE
  // ==========================================================

  function isActive(
    href: string
  ) {

    if (href === "/") {

      return pathname === "/";

    }


    return (
      pathname === href ||
      pathname.startsWith(
        `${href}/`
      )
    );

  }


  return (

    <>

      {/* ======================================================
          DESKTOP / GLOBAL NAV
          ====================================================== */}

      <header className="sticky top-0 z-[100] border-b border-white/10 bg-[#07111f]/85 backdrop-blur-2xl">

        <div className="mx-auto flex h-[76px] max-w-7xl items-center justify-between px-5 sm:px-6">


          {/* ==================================================
              BRAND
              ================================================== */}

          <Link
            href="/"
            className="group flex items-center gap-3"
          >

            <motion.div
              whileHover={{
                scale: 1.04,
                rotate: 5,
              }}
              transition={{
                type: "spring",
                stiffness: 350,
                damping: 20,
              }}
              className="relative flex h-11 w-11 items-center justify-center rounded-2xl border border-cyan-300/20 bg-cyan-300/10"
            >

              <motion.div
                animate={{
                  opacity: [
                    0.25,
                    0.55,
                    0.25,
                  ],
                  scale: [
                    0.92,
                    1.08,
                    0.92,
                  ],
                }}
                transition={{
                  duration: 3,
                  repeat: Infinity,
                  ease: "easeInOut",
                }}
                className="absolute inset-0 rounded-2xl bg-cyan-300/10"
              />

              <Layers3 className="relative h-5 w-5 text-cyan-300" />

            </motion.div>


            <div className="hidden sm:block">

              <p className="text-[13px] font-semibold tracking-[0.24em] text-white">
                JOURNEY
              </p>

              <p className="text-[10px] tracking-[0.34em] text-cyan-300/70">
                FORENSICS
              </p>

            </div>

          </Link>


          {/* ==================================================
              DESKTOP LINKS
              ================================================== */}

          <nav className="hidden items-center gap-1 lg:flex">

            {navigationItems.map(
              (
                item
              ) => {

                const Icon =
                  item.icon;

                const active =
                  isActive(
                    item.href
                  );


                return (

                  <Link
                    key={
                      item.href
                    }
                    href={
                      item.href
                    }
                    className="relative"
                  >

                    <motion.div
                      whileHover={{
                        y: -1,
                      }}
                      className={`flex items-center gap-2 rounded-xl px-3.5 py-2.5 text-xs transition ${
                        active
                          ? "text-white"
                          : "text-white/40 hover:text-white/80"
                      }`}
                    >

                      <Icon
                        className={`h-3.5 w-3.5 ${
                          active
                            ? "text-cyan-300"
                            : "text-white/30"
                        }`}
                      />

                      {item.label}

                    </motion.div>


                    {active && (

                      <motion.div
                        layoutId="active-nav"
                        className="absolute bottom-[-1px] left-2 right-2 h-px bg-gradient-to-r from-transparent via-cyan-300 to-transparent"
                        transition={{
                          type: "spring",
                          stiffness: 450,
                          damping: 35,
                        }}
                      />

                    )}

                  </Link>

                );

              }
            )}

          </nav>


          {/* ==================================================
              API STATUS + MOBILE
              ================================================== */}

          <div className="flex items-center gap-3">


            {/* API STATUS */}

            <div
              className={`hidden items-center gap-2 rounded-full border px-3.5 py-2 text-[10px] sm:flex ${
                checkingApi
                  ? "border-amber-300/10 bg-amber-300/5 text-amber-200/70"
                  : apiOnline
                    ? "border-emerald-300/10 bg-emerald-300/5 text-emerald-200/80"
                    : "border-red-300/10 bg-red-300/5 text-red-200/80"
              }`}
            >

              <span
                className={`h-1.5 w-1.5 rounded-full ${
                  checkingApi
                    ? "animate-pulse bg-amber-300"
                    : apiOnline
                      ? "bg-emerald-400"
                      : "bg-red-400"
                }`}
              />

              {checkingApi
                ? "Checking API"
                : apiOnline
                  ? "API Connected"
                  : "API Offline"}

            </div>


            {/* MOBILE MENU BUTTON */}

            <motion.button
              type="button"
              onClick={() =>
                setMobileOpen(
                  (open) =>
                    !open
                )
              }
              whileTap={{
                scale: 0.94,
              }}
              className="flex h-10 w-10 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-white/60 lg:hidden"
              aria-label="Toggle navigation"
            >

              {mobileOpen ? (
                <X className="h-5 w-5" />
              ) : (
                <Menu className="h-5 w-5" />
              )}

            </motion.button>

          </div>

        </div>


        {/* ====================================================
            MOBILE MENU
            ==================================================== */}

        <AnimatePresence>

          {mobileOpen && (

            <motion.div
              initial={{
                opacity: 0,
                height: 0,
              }}
              animate={{
                opacity: 1,
                height: "auto",
              }}
              exit={{
                opacity: 0,
                height: 0,
              }}
              className="overflow-hidden border-t border-white/10 lg:hidden"
            >

              <div className="mx-auto max-w-7xl px-5 py-4 sm:px-6">

                <div className="grid gap-2">

                  {navigationItems.map(
                    (
                      item,
                      index
                    ) => {

                      const Icon =
                        item.icon;

                      const active =
                        isActive(
                          item.href
                        );


                      return (

                        <motion.div
                          key={
                            item.href
                          }
                          initial={{
                            opacity: 0,
                            x: -10,
                          }}
                          animate={{
                            opacity: 1,
                            x: 0,
                          }}
                          transition={{
                            delay:
                              index *
                              0.035,
                          }}
                        >

                          <Link
                            href={
                              item.href
                            }
                          >

                            <div
                              className={`flex items-center gap-3 rounded-2xl px-4 py-3.5 text-sm ${
                                active
                                  ? "bg-cyan-300/10 text-cyan-200"
                                  : "bg-white/[0.025] text-white/50"
                              }`}
                            >

                              <Icon className="h-4 w-4" />

                              <span>
                                {
                                  item.label
                                }
                              </span>

                            </div>

                          </Link>

                        </motion.div>

                      );

                    }
                  )}

                </div>


                {/* MOBILE STATUS */}

                <div className="mt-4 flex items-center justify-between rounded-2xl border border-white/10 bg-white/[0.025] px-4 py-3">

                  <span className="text-xs text-white/30">
                    Analytics engine
                  </span>


                  <span className="flex items-center gap-2 text-xs">

                    <span
                      className={`h-1.5 w-1.5 rounded-full ${
                        checkingApi
                          ? "animate-pulse bg-amber-300"
                          : apiOnline
                            ? "bg-emerald-400"
                            : "bg-red-400"
                      }`}
                    />

                    {checkingApi
                      ? "Checking"
                      : apiOnline
                        ? "Online"
                        : "Offline"}

                  </span>

                </div>

              </div>

            </motion.div>

          )}

        </AnimatePresence>

      </header>

    </>
  );
}