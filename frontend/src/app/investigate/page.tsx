"use client";

import type {
  KeyboardEvent,
  ReactNode,
} from "react";

import {
  useMemo,
  useState,
} from "react";

import Link from "next/link";

import {
  AnimatePresence,
  motion,
} from "motion/react";

import {
  AlertTriangle,
  ArrowLeft,
  ArrowRight,
  BrainCircuit,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Clock3,
  Database,
  Loader2,
  Search,
  ShieldAlert,
  TrendingUp,
  XCircle,
  Zap,
} from "lucide-react";


/* ============================================================
   API CONFIG
   ============================================================ */

const API_BASE_URL =
  process.env.NEXT_PUBLIC_API_BASE_URL ||
  "http://127.0.0.1:8000";


/* ============================================================
   TYPES
   ============================================================ */

type EvidenceItem = {
  source?: string | null;
  category?: string | null;
  metric?: string | null;
  value?: unknown;
  unit?: string | null;
  detail?: string | null;
};


type StatisticalEvidence = {
  metric?: string | null;
  record_count?: number | null;
  threshold?: number | null;
  flagged_count?: number | null;
  flagged_rate?: number | null;
  source?: string | null;
};


type KPIEvidence = {
  requested_metric?: string | null;
  matched_name?: string | null;
  value?: unknown;
  status?: string | null;
  definition?: string | null;
  source?: string | null;
};


type Finding = {
  title?: string | null;
  severity?: string | null;
  metric?: string | null;
  value?: unknown;
  threshold?: number | null;
  operator?: string | null;
  evidence_sources?: string[];
  detail?: string | null;
};


type ToolResult = {
  tool_name?: string | null;
  status?: string | null;
  data?: Record<string, unknown>;
  error?: string | null;
  metadata?: Record<string, unknown>;
};


type ToolSummary = {
  total?: number;
  successful?: number;
  failed?: number;
  skipped?: number;
};


type InvestigationPlan = {
  question?: string;
  intent?: string;
  primary_metric?: string | null;
  comparison_dimension?: string | null;
  customer_id?: string | null;
  booking_id?: string | null;
  threshold?: number | null;
  threshold_operator?: string | null;
  detected_entities?: Record<string, string>;
  confidence?: number;
  tools?: unknown[];
  reasoning?: string[];
};


type InvestigationContext = {
  question?: string;
  intent?: string;
  primary_metric?: string | null;
  comparison_dimension?: string | null;
  customer_id?: string | null;
  booking_id?: string | null;
  threshold?: number | null;
  threshold_operator?: string | null;
  planner_confidence?: number;
  entities?: Record<string, string>;
  evidence?: EvidenceItem[];
  findings?: Finding[];
  statistical_evidence?: StatisticalEvidence[];
  kpi_evidence?: KPIEvidence[];
  tool_summary?: ToolSummary;
};


type InvestigationResponse = {
  question?: string;
  stage?: string;
  plan?: InvestigationPlan;
  results?: Record<string, unknown>[];
  tool_results?: ToolResult[];
  structured_context?: InvestigationContext | null;
  explanation?: string | null;
  llm_provider?: string | null;
  llm_model?: string | null;
  llm_error?: string | null;
};


/* ============================================================
   SAMPLE QUESTIONS
   ============================================================ */

const SAMPLE_QUESTIONS: string[] = [
  "What journeys are above 90 minutes?",
  "Why are payment failures increasing?",
  "Investigate booking B007998 and explain the payment journey.",
  "Why are repeat purchases falling?",
];


/* ============================================================
   FORMATTERS
   ============================================================ */

function formatValue(
  value: unknown,
): string {

  if (
    value === null ||
    value === undefined ||
    value === ""
  ) {
    return "—";
  }


  if (
    typeof value === "number" &&
    Number.isFinite(value)
  ) {

    return value.toLocaleString(
      undefined,
      {
        maximumFractionDigits: 2,
      },
    );
  }


  return String(value);
}


function formatIntent(
  value?: string | null,
): string {

  if (!value) {
    return "Investigation";
  }


  return value
    .replaceAll(
      "_",
      " ",
    )
    .toLowerCase()
    .replace(
      /\b\w/g,
      (character) =>
        character.toUpperCase(),
    );
}


/* ============================================================
   SEVERITY
   ============================================================ */

function severityClass(
  severity?: string | null,
): string {

  const normalized =
    severity
      ?.trim()
      .toUpperCase();


  if (
    normalized === "CRITICAL"
  ) {

    return (
      "border-red-400/20 " +
      "bg-red-400/10 " +
      "text-red-200"
    );
  }


  if (
    normalized === "HIGH"
  ) {

    return (
      "border-amber-400/20 " +
      "bg-amber-400/10 " +
      "text-amber-200"
    );
  }


  if (
    normalized === "MEDIUM"
  ) {

    return (
      "border-yellow-400/20 " +
      "bg-yellow-400/10 " +
      "text-yellow-200"
    );
  }


  return (
    "border-white/10 " +
    "bg-white/[0.03] " +
    "text-slate-400"
  );
}


/* ============================================================
   STATUS
   ============================================================ */

function statusClass(
  status?: string | null,
): string {

  const normalized =
    status
      ?.trim()
      .toUpperCase()
      .replaceAll(
        " ",
        "_",
      );


  if (
    normalized === "SUCCESS" ||
    normalized === "AVAILABLE"
  ) {

    return (
      "border-emerald-400/20 " +
      "bg-emerald-400/10 " +
      "text-emerald-300"
    );
  }


  if (
    normalized === "FAILED" ||
    normalized === "NOT_SUPPORTED" ||
    normalized === "UNSUPPORTED"
  ) {

    return (
      "border-red-400/20 " +
      "bg-red-400/10 " +
      "text-red-300"
    );
  }


  if (
    normalized === "PROXY"
  ) {

    return (
      "border-amber-400/20 " +
      "bg-amber-400/10 " +
      "text-amber-300"
    );
  }


  return (
    "border-white/10 " +
    "bg-white/[0.03] " +
    "text-slate-400"
  );
}


/* ============================================================
   MAIN PAGE
   ============================================================ */

export default function InvestigatePage() {

  const [
    question,
    setQuestion,
  ] = useState<string>(
    SAMPLE_QUESTIONS[0] ??
      "What journeys are above 90 minutes?",
  );


  const [
    response,
    setResponse,
  ] = useState<InvestigationResponse | null>(
    null,
  );


  const [
    loading,
    setLoading,
  ] = useState<boolean>(
    false,
  );


  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  const [
    includeExplanation,
    setIncludeExplanation,
  ] = useState<boolean>(
    true,
  );


  const [
    expandedEvidence,
    setExpandedEvidence,
  ] = useState<boolean>(
    false,
  );


  /* ==========================================================
     DERIVED DATA
     ========================================================== */

  const context =
    response?.structured_context ??
    null;


  const findings =
    useMemo<Finding[]>(
      () =>
        context?.findings ??
        [],
      [
        context,
      ],
    );


  const evidence =
    context?.evidence ?? [];


  const statisticalEvidence =
    context?.statistical_evidence ??
    [];


  const kpiEvidence =
    context?.kpi_evidence ??
    [];


  const toolResults =
    response?.tool_results ?? [];


  const toolSummary =
    context?.tool_summary;


  const visibleEvidence =
    expandedEvidence
      ? evidence
      : evidence.slice(
          0,
          8,
        );


  const successfulTools =
    toolResults.filter(
      (
        item,
      ) =>
        item.status
          ?.toUpperCase() ===
        "SUCCESS",
    ).length;


  const investigationReady =
    response?.stage ===
      "results_ready" ||
    response?.stage ===
      "explanation_ready";


  const explanationReady =
    Boolean(
      response?.explanation &&
      response.explanation.trim(),
    );


  const riskLabel =
    useMemo<string>(() => {

      const hasCritical =
        findings.some(
          (
            item,
          ) =>
            item.severity
              ?.toUpperCase() ===
            "CRITICAL",
        );


      if (
        hasCritical
      ) {
        return "CRITICAL";
      }


      const hasHigh =
        findings.some(
          (
            item,
          ) =>
            item.severity
              ?.toUpperCase() ===
            "HIGH",
        );


      if (
        hasHigh
      ) {
        return "HIGH";
      }


      return "MONITORED";

    }, [
      findings,
    ]);


  const riskTone =
    riskLabel === "CRITICAL"
      ? "text-red-300"
      : riskLabel === "HIGH"
        ? "text-amber-300"
        : "text-emerald-300";


  /* ==========================================================
     INVESTIGATE
     ========================================================== */

  async function investigate(): Promise<void> {

    const cleaned =
      question.trim();


    if (
      cleaned.length < 3
    ) {

      setError(
        "Please enter a business investigation question.",
      );

      return;
    }


    setLoading(
      true,
    );

    setError(
      null,
    );

    setResponse(
      null,
    );

    setExpandedEvidence(
      false,
    );


    try {

      const apiResponse =
        await fetch(
          `${API_BASE_URL}/ai/investigate`,
          {
            method:
              "POST",

            headers: {
              "Content-Type":
                "application/json",
            },

            body: JSON.stringify({
              question:
                cleaned,

              include_explanation:
                includeExplanation,
            }),
          },
        );


      if (
        !apiResponse.ok
      ) {

        let message =
          "Investigation request failed.";


        try {

          const errorPayload =
            (await apiResponse.json()) as {
              detail?: unknown;
              message?: unknown;
            };


          if (
            typeof errorPayload.detail ===
            "string"
          ) {

            message =
              errorPayload.detail;

          } else if (
            typeof errorPayload.message ===
            "string"
          ) {

            message =
              errorPayload.message;
          }

        } catch {
          // Keep default message.
        }


        throw new Error(
          message,
        );
      }


      const payload =
        (await apiResponse.json()) as InvestigationResponse;


      setResponse(
        payload,
      );

    } catch (
      requestError
    ) {

      if (
        requestError instanceof Error
      ) {

        setError(
          requestError.message,
        );

      } else {

        setError(
          "Unable to complete the investigation.",
        );
      }

    } finally {

      setLoading(
        false,
      );
    }
  }


  /* ==========================================================
     KEYBOARD
     ========================================================== */

  function handleKeyDown(
    event: KeyboardEvent<HTMLTextAreaElement>,
  ): void {

    if (
      event.key ===
        "Enter" &&
      (
        event.ctrlKey ||
        event.metaKey
      )
    ) {

      event.preventDefault();

      void investigate();
    }
  }


  /* ==========================================================
     RENDER
     ========================================================== */

  return (

    <main className="relative min-h-screen overflow-hidden bg-[#06101d] text-white">


      {/* ======================================================
          FORENSIC BACKGROUND
          ====================================================== */}

      <div
        className="pointer-events-none fixed inset-0 overflow-hidden"
        aria-hidden="true"
      >

        <div className="absolute inset-0 bg-[radial-gradient(circle_at_10%_12%,rgba(34,211,238,0.06),transparent_27%),radial-gradient(circle_at_88%_30%,rgba(139,92,246,0.065),transparent_30%),radial-gradient(circle_at_55%_100%,rgba(59,130,246,0.035),transparent_28%)]" />


        <div
          className="absolute inset-0 opacity-[0.04]"
          style={{
            backgroundImage:
              "linear-gradient(rgba(103,232,249,.18) 1px, transparent 1px), linear-gradient(90deg, rgba(103,232,249,.18) 1px, transparent 1px)",
            backgroundSize:
              "72px 72px",
            maskImage:
              "radial-gradient(circle at center, black 15%, transparent 84%)",
            WebkitMaskImage:
              "radial-gradient(circle at center, black 15%, transparent 84%)",
          }}
        />


        <motion.div
          className="absolute -left-48 top-24 h-[34rem] w-[34rem] rounded-full bg-cyan-400/[0.055] blur-3xl"
          animate={{
            x: [
              0,
              65,
              0,
            ],
            y: [
              0,
              35,
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


        <motion.div
          className="absolute right-[-180px] top-[38%] h-[38rem] w-[38rem] rounded-full bg-violet-500/[0.06] blur-3xl"
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
              1.12,
              1,
            ],
          }}
          transition={{
            duration: 17,
            repeat: Infinity,
            ease: "easeInOut",
          }}
        />


        <div className="absolute left-[7%] top-[32%] hidden h-64 w-64 lg:block">

          <motion.div
            className="absolute inset-0 rounded-full border border-cyan-300/[0.065]"
            animate={{
              scale: [
                0.82,
                1.05,
                0.82,
              ],
              opacity: [
                0.2,
                0.55,
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
            className="absolute inset-8 rounded-full border border-cyan-300/[0.045]"
            animate={{
              rotate: 360,
            }}
            transition={{
              duration: 28,
              repeat: Infinity,
              ease: "linear",
            }}
          />


          <span className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-300/50 shadow-[0_0_18px_rgba(103,232,249,.45)]" />

        </div>


        <div className="absolute right-[6%] top-[22%] hidden h-80 w-80 lg:block">

          <motion.div
            className="absolute inset-0 rounded-full border border-violet-300/[0.06]"
            animate={{
              scale: [
                0.8,
                1.05,
                0.8,
              ],
              opacity: [
                0.15,
                0.45,
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
            className="absolute inset-10 rounded-full border border-violet-300/[0.045]"
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


        <motion.div
          className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-cyan-300/15 to-transparent"
          animate={{
            top: [
              "8%",
              "92%",
              "8%",
            ],
          }}
          transition={{
            duration: 20,
            repeat: Infinity,
            ease: "linear",
          }}
        />


        <motion.div
          className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-violet-300/10 to-transparent"
          animate={{
            top: [
              "75%",
              "18%",
              "75%",
            ],
          }}
          transition={{
            duration: 24,
            repeat: Infinity,
            ease: "linear",
          }}
        />


        <div className="absolute inset-0">

          {Array.from({
            length: 12,
          }).map(
            (
              _,
              index,
            ) => {

              const left =
                `${8 + (index * 7.3) % 88}%`;

              const top =
                `${14 + (index * 13.7) % 72}%`;

              return (

                <motion.span
                  key={index}
                  className="absolute h-1.5 w-1.5 rounded-full bg-cyan-200/25"
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
                      0.08,
                      0.42,
                      0.08,
                    ],

                    scale: [
                      0.8,
                      1.15,
                      0.8,
                    ],
                  }}
                  transition={{
                    duration:
                      5.5 +
                      index *
                        0.22,

                    delay:
                      index *
                      0.35,

                    repeat:
                      Infinity,

                    ease:
                      "easeInOut",
                  }}
                />

              );
            },
          )}

        </div>


        <div className="absolute left-[5%] top-[63%] hidden h-8 w-8 opacity-20 lg:block">

          <span className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-cyan-300/50" />

          <span className="absolute left-0 top-1/2 h-px w-full -translate-y-1/2 bg-cyan-300/50" />

          <span className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full border border-cyan-300/60" />

        </div>


        <div className="absolute right-[5%] bottom-[20%] hidden h-8 w-8 opacity-15 lg:block">

          <span className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-violet-300/50" />

          <span className="absolute left-0 top-1/2 h-px w-full -translate-y-1/2 bg-violet-300/50" />

          <span className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full border border-violet-300/60" />

        </div>

      </div>


      {/* ======================================================
          CONTENT
          ====================================================== */}

      <section className="relative z-10 mx-auto max-w-7xl px-6 py-10">


        {/* ====================================================
            BACK
            ==================================================== */}

        <Link
          href="/"
          className="inline-flex items-center gap-2 text-sm text-white/40 transition hover:text-white"
        >

          <ArrowLeft
            size={15}
          />

          Back to overview

        </Link>


        {/* ====================================================
            HERO
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
          transition={{
            duration: 0.55,
          }}
          className="mt-8 max-w-5xl"
        >

          <div className="flex items-center gap-2 text-sm text-cyan-300/80">

            <BrainCircuit
              size={16}
            />

            AI investigation engine

          </div>


          <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl lg:text-6xl">

            Ask the evidence.

            <span className="block bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400 bg-clip-text text-transparent">
              Follow the story.
            </span>

          </h1>


          <p className="mt-5 max-w-3xl text-base leading-7 text-white/45">

            Turn a business question into a deterministic
            investigation and translate validated evidence
            into a grounded analytical conclusion.

          </p>

        </motion.div>


        {/* ====================================================
            INPUT
            ==================================================== */}

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
            delay: 0.08,
            duration: 0.5,
          }}
          className="group relative mt-9 overflow-hidden rounded-[2rem] border border-white/10 bg-[#101b2a]/80 shadow-[0_20px_60px_rgba(0,0,0,0.16)] backdrop-blur-2xl"
        >

          <div className="pointer-events-none absolute -right-24 -top-24 h-56 w-56 rounded-full bg-cyan-300/[0.05] blur-3xl transition duration-500 group-hover:bg-cyan-300/[0.075]" />


          <div className="relative p-6 md:p-8">

            <div className="mb-4 flex items-center justify-between gap-3">

              <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.18em] text-slate-500">

                <Search
                  size={15}
                />

                Investigation question

              </div>


              <span className="rounded-full border border-white/10 bg-white/[0.025] px-3 py-1.5 text-[10px] text-slate-500">

                Ctrl + Enter

              </span>

            </div>


            <textarea
              value={
                question
              }
              onChange={(
                event,
              ) =>
                setQuestion(
                  event.target.value,
                )
              }
              onKeyDown={
                handleKeyDown
              }
              rows={4}
              placeholder="Ask a business investigation question..."
              className="w-full resize-none rounded-2xl border border-white/10 bg-[#091421] px-5 py-4 text-base leading-7 text-white outline-none transition placeholder:text-slate-600 focus:border-cyan-400/45 focus:ring-4 focus:ring-cyan-400/10"
            />


            <div className="mt-4">

              <p className="mb-2 text-[10px] uppercase tracking-wider text-white/20">
                Suggested investigations
              </p>


              <div className="flex flex-wrap gap-2">

                {SAMPLE_QUESTIONS.map(
                  (
                    sample,
                  ) => (

                    <button
                      key={
                        sample
                      }
                      type="button"
                      onClick={() =>
                        setQuestion(
                          sample,
                        )
                      }
                      className={`rounded-full border px-3 py-2 text-xs transition ${
                        question ===
                        sample
                          ? "border-cyan-400/25 bg-cyan-400/10 text-cyan-200"
                          : "border-white/10 bg-white/[0.025] text-slate-400 hover:border-cyan-400/20 hover:text-cyan-200"
                      }`}
                    >
                      {sample}
                    </button>

                  ),
                )}

              </div>

            </div>


            <div className="mt-6 flex flex-col gap-4 border-t border-white/10 pt-5 md:flex-row md:items-center md:justify-between">

              <button
                type="button"
                onClick={() =>
                  setIncludeExplanation(
                    (
                      current,
                    ) =>
                      !current,
                  )
                }
                className="flex items-center gap-3 text-left"
                aria-pressed={
                  includeExplanation
                }
              >

                <span
                  className={`relative h-6 w-11 rounded-full transition ${
                    includeExplanation
                      ? "bg-cyan-400/80"
                      : "bg-slate-700"
                  }`}
                >

                  <motion.span
                    layout
                    className={`absolute top-1 h-4 w-4 rounded-full bg-white ${
                      includeExplanation
                        ? "left-6"
                        : "left-1"
                    }`}
                  />

                </span>


                <span>

                  <span className="block text-sm text-slate-300">
                    Generate AI explanation
                  </span>

                  <span className="block text-xs text-slate-600">
                    Keep the deterministic evidence layer intact.
                  </span>

                </span>

              </button>


              <motion.button
                type="button"
                onClick={() =>
                  void investigate()
                }
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
                      : "0 0 34px rgba(103,232,249,0.14)",
                }}
                whileTap={{
                  scale:
                    loading
                      ? 1
                      : 0.98,
                }}
                className="inline-flex min-h-[54px] items-center justify-center gap-3 rounded-2xl bg-gradient-to-r from-cyan-300 to-sky-400 px-7 font-semibold text-[#06101d] transition disabled:cursor-not-allowed disabled:opacity-60"
              >

                {loading ? (
                  <>
                    <Loader2
                      size={18}
                      className="animate-spin"
                    />

                    Investigating...
                  </>
                ) : (
                  <>
                    Investigate evidence

                    <ArrowRight
                      size={18}
                    />
                  </>
                )}

              </motion.button>

            </div>

          </div>


          {/* ==================================================
              LOADING PIPELINE
              ================================================== */}

          <AnimatePresence>

            {loading && (

              <motion.div
                initial={{
                  height: 0,
                  opacity: 0,
                }}
                animate={{
                  height: "auto",
                  opacity: 1,
                }}
                exit={{
                  height: 0,
                  opacity: 0,
                }}
                className="border-t border-cyan-400/10 bg-cyan-400/[0.025]"
              >

                <div className="grid gap-3 p-6 md:grid-cols-4">

                  {[
                    {
                      label:
                        "Planning",
                      icon:
                        BrainCircuit,
                    },
                    {
                      label:
                        "Collecting evidence",
                      icon:
                        Database,
                    },
                    {
                      label:
                        "Reconciling signals",
                      icon:
                        TrendingUp,
                    },
                    {
                      label:
                        "Grounding explanation",
                      icon:
                        ShieldAlert,
                    },
                  ].map(
                    (
                      item,
                      index,
                    ) => {

                      const Icon =
                        item.icon;


                      return (

                        <motion.div
                          key={
                            item.label
                          }
                          initial={{
                            opacity: 0,
                            y: 8,
                          }}
                          animate={{
                            opacity: 1,
                            y: 0,
                          }}
                          transition={{
                            delay:
                              index *
                              0.11,
                          }}
                          className="flex items-center gap-3 rounded-2xl border border-white/10 bg-white/[0.025] p-4"
                        >

                          <motion.div
                            animate={{
                              scale: [
                                1,
                                1.08,
                                1,
                              ],
                              opacity: [
                                0.65,
                                1,
                                0.65,
                              ],
                            }}
                            transition={{
                              duration:
                                1.2,
                              repeat:
                                Infinity,
                              delay:
                                index *
                                0.15,
                            }}
                            className="flex h-9 w-9 items-center justify-center rounded-xl bg-cyan-400/10 text-cyan-300"
                          >

                            <Icon
                              size={17}
                            />

                          </motion.div>


                          <span className="text-sm text-slate-300">
                            {
                              item.label
                            }
                          </span>

                        </motion.div>

                      );

                    },
                  )}

                </div>

              </motion.div>

            )}

          </AnimatePresence>

        </motion.section>


        {/* ====================================================
            ERROR
            ==================================================== */}

        <AnimatePresence>

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
              exit={{
                opacity: 0,
                y: -10,
              }}
              className="mt-6 flex items-start gap-3 rounded-2xl border border-red-400/20 bg-red-400/[0.06] p-5"
            >

              <XCircle
                size={20}
                className="mt-0.5 shrink-0 text-red-300"
              />


              <div>

                <div className="font-semibold text-red-100">
                  Investigation unavailable
                </div>


                <div className="mt-1 text-sm text-red-200/65">
                  {error}
                </div>

              </div>

            </motion.div>

          )}

        </AnimatePresence>


        {/* ====================================================
            RESULTS
            ==================================================== */}

        <AnimatePresence mode="wait">

          {response &&
            investigationReady && (

            <motion.div
              key="results"
              initial={{
                opacity: 0,
                y: 24,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              transition={{
                duration: 0.55,
              }}
              className="mt-8 space-y-6"
            >


              {/* ==================================================
                  INVESTIGATION HEADER
                  ================================================== */}

              <section className="relative overflow-hidden rounded-[2rem] border border-emerald-400/10 bg-[#101b2a]/85 p-6 backdrop-blur-2xl md:p-8">

                <div className="pointer-events-none absolute -right-20 -top-20 h-48 w-48 rounded-full bg-emerald-300/[0.035] blur-3xl" />


                <div className="relative flex flex-col gap-6 lg:flex-row lg:items-center lg:justify-between">

                  <div>

                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-emerald-300">

                      <CheckCircle2
                        size={15}
                      />

                      Investigation complete

                    </div>


                    <h2 className="mt-2 max-w-4xl text-2xl font-semibold leading-tight">
                      {
                        context?.question ||
                        response.question ||
                        "Investigation"
                      }
                    </h2>


                    <div className="mt-4 flex flex-wrap gap-2">

                      <span className="rounded-full border border-cyan-400/20 bg-cyan-400/5 px-3 py-1.5 text-xs text-cyan-200">
                        {
                          formatIntent(
                            context?.intent,
                          )
                        }
                      </span>


                      {context?.primary_metric && (

                        <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-400">
                          Metric:{" "}
                          {
                            context.primary_metric
                          }
                        </span>

                      )}


                      {context?.comparison_dimension && (

                        <span className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-400">
                          By{" "}
                          {
                            context.comparison_dimension
                          }
                        </span>

                      )}


                      {context?.threshold !==
                        null &&
                        context?.threshold !==
                          undefined && (

                        <span className="rounded-full border border-amber-400/20 bg-amber-400/5 px-3 py-1.5 text-xs text-amber-200">

                          Threshold{" "}

                          {
                            context.threshold_operator ||
                            ">="
                          }{" "}

                          {
                            context.threshold
                          }

                        </span>

                      )}

                    </div>

                  </div>


                  <div className="shrink-0 rounded-3xl border border-white/10 bg-black/10 px-6 py-5">

                    <p className="text-[10px] uppercase tracking-[0.15em] text-slate-600">
                      Investigation pressure
                    </p>


                    <div className="mt-2 flex items-center gap-2">

                      <ShieldAlert
                        size={18}
                        className={
                          riskTone
                        }
                      />


                      <span
                        className={`text-xl font-semibold ${riskTone}`}
                      >
                        {riskLabel}
                      </span>

                    </div>


                    {context?.planner_confidence !==
                      null &&
                      context?.planner_confidence !==
                        undefined && (

                      <p className="mt-2 text-xs text-slate-600">

                        Planner confidence{" "}

                        {(
                          context.planner_confidence *
                          100
                        ).toFixed(0)}
                        %

                      </p>

                    )}

                  </div>

                </div>

              </section>


              {/* ==================================================
                  KPI SUMMARY CARDS
                  ================================================== */}

              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">

                <MetricCard
                  icon={
                    <Zap
                      size={18}
                    />
                  }
                  label="Tools executed"
                  value={
                    toolSummary?.total ??
                    toolResults.length
                  }
                  caption={`${successfulTools} successful`}
                />


                <MetricCard
                  icon={
                    <Database
                      size={18}
                    />
                  }
                  label="Evidence items"
                  value={
                    evidence.length
                  }
                  caption="Source-aware evidence"
                />


                <MetricCard
                  icon={
                    <TrendingUp
                      size={18}
                    />
                  }
                  label="Findings"
                  value={
                    findings.length
                  }
                  caption="Prioritized signals"
                />


                <MetricCard
                  icon={
                    <Clock3
                      size={18}
                    />
                  }
                  label="AI state"
                  value={
                    response.stage ===
                    "explanation_ready"
                      ? "Ready"
                      : "Evidence"
                  }
                  caption={
                    response.stage ??
                    "results_ready"
                  }
                />

              </div>


              {/* ==================================================
                  FINDINGS + STATISTICS
                  ================================================== */}

              <div className="grid gap-6 lg:grid-cols-[1.45fr_0.85fr]">


                {/* FINDINGS */}

                <section className="rounded-[2rem] border border-white/10 bg-[#101b2a]/85 p-6 backdrop-blur-2xl">

                  <div className="mb-5 flex items-center justify-between gap-4">

                    <div>

                      <div className="text-xs font-semibold uppercase tracking-[0.16em] text-red-300/80">
                        Investigation findings
                      </div>


                      <h3 className="mt-1 text-xl font-semibold">
                        What needs attention
                      </h3>

                    </div>


                    <div className="rounded-full border border-white/10 bg-white/[0.03] px-3 py-1.5 text-xs text-slate-500">

                      {
                        findings.length
                      }{" "}
                      signals

                    </div>

                  </div>


                  {findings.length ===
                  0 ? (

                    <EmptyState
                      icon={
                        <CheckCircle2
                          size={21}
                        />
                      }
                      title="No high-priority finding"
                      description="The deterministic investigation did not surface a prioritized issue."
                    />

                  ) : (

                    <div className="space-y-3">

                      {findings.map(
                        (
                          finding,
                          index,
                        ) => (

                          <motion.div
                            key={`${finding.title ?? "finding"}-${index}`}
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
                                0.055,
                            }}
                            whileHover={{
                              x: 3,
                            }}
                            className="group rounded-2xl border border-white/10 bg-[#0b1624] p-5 transition hover:border-red-300/10"
                          >

                            <div className="flex items-start gap-4">

                              <div className="mt-1 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl bg-red-400/10 text-red-300">

                                <AlertTriangle
                                  size={18}
                                />

                              </div>


                              <div className="min-w-0 flex-1">

                                <div className="flex flex-col gap-2 sm:flex-row sm:items-center sm:justify-between">

                                  <h4 className="font-semibold text-slate-100">
                                    {
                                      finding.title ||
                                      "Investigation finding"
                                    }
                                  </h4>


                                  <span
                                    className={`w-fit rounded-full border px-2.5 py-1 text-[10px] font-bold tracking-wide ${severityClass(
                                      finding.severity,
                                    )}`}
                                  >
                                    {
                                      finding.severity ||
                                      "INFO"
                                    }
                                  </span>

                                </div>


                                {finding.detail && (

                                  <p className="mt-2 text-sm leading-6 text-slate-400">
                                    {
                                      finding.detail
                                    }
                                  </p>

                                )}


                                <div className="mt-3 flex flex-wrap gap-2">

                                  {finding.metric && (

                                    <span className="rounded-lg border border-white/10 bg-white/[0.025] px-2.5 py-1 text-xs text-slate-400">
                                      {
                                        finding.metric
                                      }
                                    </span>

                                  )}


                                  {finding.value !==
                                    undefined &&
                                    finding.value !==
                                      null && (

                                    <span className="rounded-lg border border-cyan-400/10 bg-cyan-400/5 px-2.5 py-1 text-xs text-cyan-200">

                                      Value:{" "}

                                      {
                                        formatValue(
                                          finding.value,
                                        )
                                      }

                                    </span>

                                  )}


                                  {finding.threshold !==
                                    null &&
                                    finding.threshold !==
                                      undefined && (

                                    <span className="rounded-lg border border-amber-400/10 bg-amber-400/5 px-2.5 py-1 text-xs text-amber-200">

                                      Threshold{" "}

                                      {
                                        finding.operator ||
                                        ">="
                                      }{" "}

                                      {
                                        finding.threshold
                                      }

                                    </span>

                                  )}

                                </div>

                              </div>

                            </div>

                          </motion.div>

                        ),
                      )}

                    </div>

                  )}

                </section>


                {/* STATISTICS */}

                <section className="rounded-[2rem] border border-white/10 bg-[#101b2a]/85 p-6 backdrop-blur-2xl">

                  <div className="mb-5">

                    <div className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300/80">
                      Statistical signal
                    </div>


                    <h3 className="mt-1 text-xl font-semibold">
                      Validated evidence
                    </h3>

                  </div>


                  {statisticalEvidence.length ===
                  0 ? (

                    <EmptyState
                      icon={
                        <Database
                          size={21}
                        />
                      }
                      title="No statistical evidence"
                      description="No statistical analysis result was returned for this investigation."
                    />

                  ) : (

                    <div className="space-y-3">

                      {statisticalEvidence.map(
                        (
                          statistic,
                          index,
                        ) => (

                          <div
                            key={`${statistic.metric ?? "metric"}-${index}`}
                            className="rounded-2xl border border-white/10 bg-[#0b1624] p-4"
                          >

                            <div className="flex items-center justify-between gap-4">

                              <span className="text-sm text-slate-500">
                                Metric
                              </span>


                              <span className="max-w-[60%] text-right text-sm font-medium text-cyan-200">
                                {
                                  statistic.metric ||
                                  "—"
                                }
                              </span>

                            </div>


                            <div className="my-4 h-px bg-white/5" />


                            <StatLine
                              label="Records"
                              value={
                                formatValue(
                                  statistic.record_count,
                                )
                              }
                            />


                            <StatLine
                              label="Threshold"
                              value={
                                formatValue(
                                  statistic.threshold,
                                )
                              }
                            />


                            <StatLine
                              label="Flagged"
                              value={
                                formatValue(
                                  statistic.flagged_count,
                                )
                              }
                            />


                            <StatLine
                              label="Flagged rate"
                              value={
                                statistic.flagged_rate !==
                                  null &&
                                statistic.flagged_rate !==
                                  undefined
                                  ? `${formatValue(
                                      statistic.flagged_rate,
                                    )}%`
                                  : "—"
                              }
                            />

                          </div>

                        ),
                      )}

                    </div>

                  )}

                </section>

              </div>


              {/* ==================================================
                  KPI + TOOL TRACE
                  ================================================== */}

              <div className="grid gap-6 lg:grid-cols-2">


                {/* KPI */}

                <section className="rounded-[2rem] border border-white/10 bg-[#101b2a]/85 p-6 backdrop-blur-2xl">

                  <div className="mb-5">

                    <div className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300/80">
                      KPI intelligence
                    </div>


                    <h3 className="mt-1 text-xl font-semibold">
                      Validated business signals
                    </h3>

                  </div>


                  {kpiEvidence.length ===
                  0 ? (

                    <EmptyState
                      icon={
                        <TrendingUp
                          size={21}
                        />
                      }
                      title="No KPI evidence selected"
                      description="This investigation did not require a KPI lookup."
                    />

                  ) : (

                    <div className="space-y-3">

                      {kpiEvidence.map(
                        (
                          kpi,
                          index,
                        ) => (

                          <motion.div
                            key={`${kpi.requested_metric ?? "kpi"}-${index}`}
                            whileHover={{
                              y: -2,
                            }}
                            className="rounded-2xl border border-white/10 bg-[#0b1624] p-4"
                          >

                            <div className="flex items-start justify-between gap-4">

                              <div className="min-w-0">

                                <div className="font-medium text-slate-200">
                                  {
                                    kpi.matched_name ||
                                    kpi.requested_metric ||
                                    "Validated KPI"
                                  }
                                </div>


                                <div className="mt-1 text-xs leading-5 text-slate-500">
                                  {
                                    kpi.definition ||
                                    "Validated KPI"
                                  }
                                </div>

                              </div>


                              <span
                                className={`shrink-0 rounded-full border px-2.5 py-1 text-[10px] font-bold ${statusClass(
                                  kpi.status,
                                )}`}
                              >
                                {
                                  kpi.status ||
                                  "UNKNOWN"
                                }
                              </span>

                            </div>


                            <div className="mt-4 text-2xl font-semibold text-white">
                              {
                                formatValue(
                                  kpi.value,
                                )
                              }
                            </div>

                          </motion.div>

                        ),
                      )}

                    </div>

                  )}

                </section>


                {/* TOOL TRACE */}

                <section className="rounded-[2rem] border border-white/10 bg-[#101b2a]/85 p-6 backdrop-blur-2xl">

                  <div className="mb-5 flex items-center justify-between gap-4">

                    <div>

                      <div className="text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300/80">
                        Investigation trace
                      </div>


                      <h3 className="mt-1 text-xl font-semibold">
                        Tool execution
                      </h3>

                    </div>


                    <div className="flex items-center gap-2 text-xs text-emerald-300">

                      <CheckCircle2
                        size={14}
                      />

                      {
                        successfulTools
                      }{" "}
                      successful

                    </div>

                  </div>


                  {toolResults.length ===
                  0 ? (

                    <EmptyState
                      icon={
                        <Zap
                          size={21}
                        />
                      }
                      title="No tool trace"
                      description="No tool execution records were returned."
                    />

                  ) : (

                    <div className="space-y-2">

                      {toolResults.map(
                        (
                          tool,
                          index,
                        ) => (

                          <motion.div
                            key={`${tool.tool_name ?? "tool"}-${index}`}
                            initial={{
                              opacity: 0,
                              x: 8,
                            }}
                            animate={{
                              opacity: 1,
                              x: 0,
                            }}
                            transition={{
                              delay:
                                index *
                                0.045,
                            }}
                            className="flex items-center justify-between rounded-2xl border border-white/10 bg-[#0b1624] p-4"
                          >

                            <div className="flex min-w-0 items-center gap-3">

                              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-white/[0.04] text-cyan-300">

                                <Zap
                                  size={16}
                                />

                              </div>


                              <span className="truncate text-sm text-slate-300">
                                {
                                  tool.tool_name ||
                                  "tool"
                                }
                              </span>

                            </div>


                            <span
                              className={`rounded-full border px-2.5 py-1 text-[10px] font-bold ${statusClass(
                                tool.status,
                              )}`}
                            >
                              {
                                tool.status ||
                                "UNKNOWN"
                              }
                            </span>

                          </motion.div>

                        ),
                      )}

                    </div>

                  )}

                </section>

              </div>


              {/* ==================================================
                  EVIDENCE CHAIN
                  ================================================== */}

              <section className="rounded-[2rem] border border-white/10 bg-[#101b2a]/85 p-6 backdrop-blur-2xl md:p-8">

                <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">

                  <div>

                    <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300/80">

                      <Database
                        size={15}
                      />

                      Evidence chain

                    </div>


                    <h3 className="mt-1 text-xl font-semibold">
                      Source-aware investigation evidence
                    </h3>


                    <p className="mt-1 text-xs text-slate-600">
                      Every displayed signal remains tied to returned evidence.
                    </p>

                  </div>


                  {evidence.length >
                    8 && (

                    <button
                      type="button"
                      onClick={() =>
                        setExpandedEvidence(
                          (
                            current,
                          ) =>
                            !current,
                        )
                      }
                      className="inline-flex items-center justify-center gap-2 rounded-xl border border-white/10 bg-white/[0.03] px-4 py-2.5 text-sm text-slate-300 transition hover:border-cyan-400/20 hover:text-white"
                    >

                      {expandedEvidence
                        ? "Collapse"
                        : "View all"}

                      {expandedEvidence ? (
                        <ChevronUp
                          size={16}
                        />
                      ) : (
                        <ChevronDown
                          size={16}
                        />
                      )}

                    </button>

                  )}

                </div>


                {evidence.length ===
                0 ? (

                  <div className="mt-5">

                    <EmptyState
                      icon={
                        <Database
                          size={21}
                        />
                      }
                      title="No evidence returned"
                      description="The investigation completed without source evidence."
                    />

                  </div>

                ) : (

                  <div className="mt-5 grid gap-3 md:grid-cols-2">

                    {visibleEvidence.map(
                      (
                        item,
                        index,
                      ) => (

                        <motion.div
                          key={`${item.source ?? "source"}-${item.metric ?? "metric"}-${index}`}
                          whileHover={{
                            y: -2,
                          }}
                          className="rounded-2xl border border-white/10 bg-[#0b1624] p-4"
                        >

                          <div className="flex items-start justify-between gap-4">

                            <div className="min-w-0">

                              <div className="text-[10px] uppercase tracking-wider text-slate-600">
                                {
                                  item.category ||
                                  "evidence"
                                }
                              </div>


                              <div className="mt-1 truncate text-sm font-medium text-slate-200">
                                {
                                  item.metric ||
                                  "Investigation signal"
                                }
                              </div>

                            </div>


                            <span className="shrink-0 rounded-full border border-white/10 bg-white/[0.03] px-2 py-1 text-[10px] text-slate-500">
                              {
                                item.source ||
                                "source"
                              }
                            </span>

                          </div>


                          <div className="mt-3 text-lg font-semibold text-white">
                            {
                              formatValue(
                                item.value,
                              )
                            }
                          </div>


                          {item.unit && (

                            <div className="mt-1 text-xs text-slate-600">
                              {
                                item.unit
                              }
                            </div>

                          )}


                          {item.detail && (

                            <p className="mt-2 text-xs leading-5 text-slate-500">
                              {
                                item.detail
                              }
                            </p>

                          )}

                        </motion.div>

                      ),
                    )}

                  </div>

                )}

              </section>


              {/* ==================================================
                  AI EXPLANATION
                  ================================================== */}

              <section className="relative overflow-hidden rounded-[2rem] border border-cyan-400/15 bg-gradient-to-br from-cyan-400/[0.07] via-[#101b2a]/90 to-indigo-500/[0.065] backdrop-blur-2xl">

                <div className="pointer-events-none absolute -right-24 -top-24 h-56 w-56 rounded-full bg-cyan-300/[0.05] blur-3xl" />


                <div className="relative p-6 md:p-8">

                  <div className="flex flex-col gap-5 md:flex-row md:items-start md:justify-between">

                    <div>

                      <div className="flex items-center gap-2 text-xs font-semibold uppercase tracking-[0.16em] text-cyan-300">

                        <BrainCircuit
                          size={16}
                        />

                        AI explanation

                      </div>


                      <h3 className="mt-2 text-2xl font-semibold">
                        What the evidence means
                      </h3>


                      <p className="mt-1 text-sm text-slate-500">
                        Grounded against the investigation evidence.
                      </p>

                    </div>


                    <div className="flex flex-wrap gap-2">

                      {response.llm_provider && (

                        <span className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-slate-500">
                          {
                            response.llm_provider
                          }
                        </span>

                      )}


                      {response.llm_model && (

                        <span className="rounded-xl border border-white/10 bg-white/[0.03] px-3 py-2 text-xs text-slate-500">
                          {
                            response.llm_model
                          }
                        </span>

                      )}

                    </div>

                  </div>


                  {!includeExplanation ? (

                    <div className="mt-6 rounded-2xl border border-white/10 bg-black/10 p-5 text-sm text-slate-400">

                      AI explanation was disabled for this investigation.

                    </div>

                  ) : explanationReady ? (

                    <motion.div
                      initial={{
                        opacity: 0,
                        y: 10,
                      }}
                      animate={{
                        opacity: 1,
                        y: 0,
                      }}
                      className="mt-6 whitespace-pre-line rounded-2xl border border-white/10 bg-[#071321]/60 p-6 text-sm leading-7 text-slate-300 md:text-base"
                    >

                      {
                        response.explanation
                      }

                    </motion.div>

                  ) : (

                    <div className="mt-6 rounded-2xl border border-amber-400/10 bg-amber-400/[0.04] p-5">

                      <div className="flex items-center gap-2 text-sm font-medium text-amber-200">

                        <AlertTriangle
                          size={17}
                        />

                        Evidence is ready; explanation is unavailable.

                      </div>


                      <p className="mt-2 text-sm leading-6 text-slate-500">
                        {
                          response.llm_error ||
                          "The deterministic investigation completed, but no LLM explanation was returned."
                        }
                      </p>

                    </div>

                  )}

                </div>

              </section>


              {/* ==================================================
                  BOTTOM ACTIONS
                  ================================================== */}

              <div className="flex flex-col gap-3 pb-8 sm:flex-row">

                <Link
                  href="/customers"
                  className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-3 text-sm text-slate-300 transition hover:border-cyan-400/20 hover:bg-white/[0.05] hover:text-white"
                >

                  Customer intelligence

                  <ArrowRight
                    size={16}
                  />

                </Link>


                <Link
                  href="/journeys"
                  className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-3 text-sm text-slate-300 transition hover:border-cyan-400/20 hover:bg-white/[0.05] hover:text-white"
                >

                  Journey forensics

                  <ArrowRight
                    size={16}
                  />

                </Link>


                <Link
                  href="/kpis"
                  className="inline-flex items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/[0.03] px-5 py-3 text-sm text-slate-300 transition hover:border-cyan-400/20 hover:bg-white/[0.05] hover:text-white"
                >

                  KPI intelligence

                  <ArrowRight
                    size={16}
                  />

                </Link>

              </div>

            </motion.div>

          )}

        </AnimatePresence>

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
            Grounded investigation intelligence
          </span>

        </div>

      </footer>

    </main>
  );
}


/* ============================================================
   METRIC CARD
   ============================================================ */

function MetricCard({
  icon,
  label,
  value,
  caption,
}: {
  icon: ReactNode;
  label: string;
  value: ReactNode;
  caption: string;
}) {

  return (

    <motion.div
      whileHover={{
        y: -4,
      }}
      transition={{
        duration: 0.2,
      }}
      className="group relative overflow-hidden rounded-3xl border border-white/10 bg-[#101b2a]/85 p-5 backdrop-blur-xl"
    >

      <div className="pointer-events-none absolute -right-10 -top-10 h-24 w-24 rounded-full bg-cyan-300/[0.04] blur-2xl transition group-hover:bg-cyan-300/[0.07]" />


      <div className="relative">

        <div className="flex h-9 w-9 items-center justify-center rounded-xl border border-white/5 bg-cyan-400/10 text-cyan-300">

          {icon}

        </div>


        <div className="mt-5 text-[10px] uppercase tracking-[0.14em] text-slate-600">
          {label}
        </div>


        <div className="mt-1 text-2xl font-semibold">
          {value}
        </div>


        <div className="mt-1 text-xs text-slate-500">
          {caption}
        </div>

      </div>

    </motion.div>
  );
}


/* ============================================================
   STAT LINE
   ============================================================ */

function StatLine({
  label,
  value,
}: {
  label: string;
  value?: string | null;
}) {

  return (

    <div className="flex items-center justify-between py-1.5">

      <span className="text-sm text-slate-500">
        {label}
      </span>


      <span className="text-sm font-medium text-slate-200">
        {value ?? "—"}
      </span>

    </div>
  );
}


/* ============================================================
   EMPTY STATE
   ============================================================ */

function EmptyState({
  icon,
  title,
  description,
}: {
  icon: ReactNode;
  title: string;
  description: string;
}) {

  return (

    <div className="rounded-2xl border border-dashed border-white/10 bg-white/[0.015] p-7">

      <div className="flex h-10 w-10 items-center justify-center rounded-xl bg-white/[0.04] text-slate-400">
        {icon}
      </div>


      <div className="mt-4 font-medium text-slate-200">
        {title}
      </div>


      <p className="mt-1 text-sm leading-6 text-slate-500">
        {description}
      </p>

    </div>
  );
}