"use client";

import Link from "next/link";

import {
  BarChart3,
  BrainCircuit,
  Database,
  Fingerprint,
  LayoutDashboard,
  UploadCloud,
  Users,
  Waves,
} from "lucide-react";

import {
  motion,
} from "motion/react";

import {
  usePathname,
} from "next/navigation";


/* ============================================================
   NAVIGATION ITEMS
   ============================================================ */

const navigation = [
  {
    href: "/",
    label: "Overview",
    icon: LayoutDashboard,
  },

  {
    href: "/customers",
    label: "Customers",
    icon: Users,
  },

  {
    href: "/journeys",
    label: "Journeys",
    icon: Waves,
  },

  {
    href: "/investigate",
    label: "Investigate",
    icon: BrainCircuit,
  },

  {
    href: "/kpis",
    label: "KPIs",
    icon: BarChart3,
  },

  {
    href: "/quality",
    label: "Quality",
    icon: Database,
  },

  {
    href: "/upload",
    label: "Upload",
    icon: UploadCloud,
  },
];


/* ============================================================
   COMPONENT
   ============================================================ */

export default function AppNavigation() {

  const pathname =
    usePathname();


  return (

    <header className="sticky top-0 z-50 border-b border-white/10 bg-[#071321]/85 shadow-lg shadow-black/10 backdrop-blur-2xl">

      <div className="mx-auto flex max-w-7xl items-center justify-between gap-4 px-4 py-3 sm:px-5 sm:py-4">


        {/* ====================================================
            BRAND
            ==================================================== */}

        <Link
          href="/"
          aria-label="Journey Forensics Overview"
          className="group flex shrink-0 items-center gap-3"
        >

          <motion.div
            whileHover={{
              scale: 1.04,
            }}
            transition={{
              duration: 0.2,
            }}
            className="flex h-10 w-10 items-center justify-center rounded-xl border border-cyan-400/25 bg-cyan-400/10 text-cyan-300 shadow-lg shadow-cyan-500/5 transition group-hover:border-cyan-300/50 group-hover:bg-cyan-400/15"
          >

            <Fingerprint
              size={20}
            />

          </motion.div>


          <div className="hidden sm:block">

            <div className="text-sm font-bold tracking-[0.28em] text-white">
              JOURNEY
            </div>

            <div className="text-[10px] font-semibold tracking-[0.36em] text-cyan-300">
              FORENSICS
            </div>

          </div>

        </Link>


        {/* ====================================================
            DESKTOP NAV
            ==================================================== */}

        <nav
          aria-label="Primary navigation"
          className="mx-auto hidden items-center rounded-2xl border border-white/5 bg-white/[0.02] p-1 lg:flex"
        >

          {navigation.map(
            ({
              href,
              label,
              icon: Icon,
            }) => {

              const active =
                href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(
                      href,
                    );


              return (

                <Link
                  key={href}
                  href={href}
                  title={label}
                  className={`group relative inline-flex items-center gap-2 rounded-xl px-3.5 py-2.5 text-xs font-medium transition ${
                    active
                      ? "bg-white/[0.05] text-white"
                      : "text-slate-500 hover:bg-white/[0.025] hover:text-slate-200"
                  }`}
                >

                  <Icon
                    size={15}
                    className={
                      active
                        ? "text-cyan-300"
                        : "text-slate-600 transition group-hover:text-cyan-300"
                    }
                  />


                  <span>
                    {label}
                  </span>


                  {active && (
                    <ActiveIndicator />
                  )}

                </Link>

              );
            },
          )}

        </nav>


        {/* ====================================================
            STATUS
            ==================================================== */}

        <div
          title="Backend API connection status"
          className="flex shrink-0 items-center gap-2 rounded-full border border-emerald-400/15 bg-emerald-400/[0.06] px-3 py-2 text-[11px] text-emerald-300 shadow-sm"
        >

          <motion.span
            className="h-2 w-2 rounded-full bg-emerald-400"
            animate={{
              opacity: [
                0.45,
                1,
                0.45,
              ],
              scale: [
                0.95,
                1.05,
                0.95,
              ],
            }}
            transition={{
              duration: 1.8,
              repeat: Infinity,
              ease: "easeInOut",
            }}
          />

          <span className="hidden sm:inline">
            API Connected
          </span>

        </div>

      </div>


      {/* ======================================================
          MOBILE NAV
          ====================================================== */}

      <div className="border-t border-white/5 bg-black/10 lg:hidden">

        <nav
          aria-label="Mobile navigation"
          className="mx-auto flex max-w-7xl gap-1 overflow-x-auto px-4 py-2.5 sm:px-5"
        >

          {navigation.map(
            ({
              href,
              label,
              icon: Icon,
            }) => {

              const active =
                href === "/"
                  ? pathname === "/"
                  : pathname.startsWith(
                      href,
                    );


              return (

                <Link
                  key={href}
                  href={href}
                  className={`inline-flex shrink-0 items-center gap-2 rounded-xl border px-3.5 py-2 text-xs font-medium transition ${
                    active
                      ? "border-cyan-400/20 bg-cyan-400/10 text-cyan-200"
                      : "border-transparent text-slate-500 hover:bg-white/[0.04] hover:text-slate-300"
                  }`}
                >

                  <Icon
                    size={14}
                    className={
                      active
                        ? "text-cyan-300"
                        : "text-slate-600"
                    }
                  />

                  <span>
                    {label}
                  </span>

                </Link>

              );
            },
          )}

        </nav>

      </div>

    </header>
  );
}


/* ============================================================
   ACTIVE INDICATOR
   ============================================================ */

function ActiveIndicator() {

  return (

    <motion.span
      layoutId="navigation-active-indicator"
      className="absolute inset-x-3 -bottom-1 h-0.5 rounded-full bg-gradient-to-r from-cyan-300 to-sky-400"
      transition={{
        type: "spring",
        stiffness: 420,
        damping: 32,
      }}
    />

  );
}