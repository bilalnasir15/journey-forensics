"use client";

import type {
  ChangeEvent,
  DragEvent,
  ReactNode,
} from "react";

import {
  ArrowLeft,
  CheckCircle2,
  CloudUpload,
  FileSpreadsheet,
  FileText,
  Loader2,
  RefreshCw,
  ShieldCheck,
  Sparkles,
  UploadCloud,
  X,
  XCircle,
} from "lucide-react";

import { motion } from "motion/react";

import Link from "next/link";

import {
  useRef,
  useState,
} from "react";

import {
  uploadCSV,
  type UploadResponse,
} from "@/lib/api";


/* ============================================================
   CONSTANTS
   ============================================================ */

const MAX_FILE_SIZE =
  10 * 1024 * 1024;

const MAX_FILE_SIZE_LABEL =
  "10 MB";


/* ============================================================
   PAGE
   ============================================================ */

export default function UploadPage() {

  /* ==========================================================
     REFS
     ========================================================== */

  const fileInputRef =
    useRef<HTMLInputElement | null>(
      null,
    );


  const progressTimerRef =
    useRef<number | null>(
      null,
    );


  /* ==========================================================
     STATE
     ========================================================== */

  const [
    selectedFile,
    setSelectedFile,
  ] = useState<File | null>(
    null,
  );


  const [
    isDragging,
    setIsDragging,
  ] = useState<boolean>(
    false,
  );


  const [
    uploading,
    setUploading,
  ] = useState<boolean>(
    false,
  );


  const [
    uploadProgress,
    setUploadProgress,
  ] = useState<number>(
    0,
  );


  const [
    result,
    setResult,
  ] = useState<UploadResponse | null>(
    null,
  );


  const [
    error,
    setError,
  ] = useState<string | null>(
    null,
  );


  /* ==========================================================
     FILE VALIDATION
     ========================================================== */

  function validateFile(
    file: File,
  ): string | null {

    if (!file) {

      return "Please select a CSV file.";

    }


    const fileName =
      file.name.toLowerCase();


    if (
      !fileName.endsWith(
        ".csv",
      )
    ) {

      return "Only CSV files are supported.";

    }


    if (
      file.size === 0
    ) {

      return "The selected file is empty.";

    }


    if (
      file.size >
      MAX_FILE_SIZE
    ) {

      return (
        `File is too large. ` +
        `Maximum size is ${MAX_FILE_SIZE_LABEL}.`
      );

    }


    return null;
  }


  /* ==========================================================
     HANDLE FILE SELECT
     ========================================================== */

  function handleFileSelect(
    file: File,
  ): void {

    setResult(
      null,
    );

    setError(
      null,
    );

    setUploadProgress(
      0,
    );


    const validationError =
      validateFile(
        file,
      );


    if (
      validationError
    ) {

      setSelectedFile(
        null,
      );

      setError(
        validationError,
      );

      return;
    }


    setSelectedFile(
      file,
    );
  }


  /* ==========================================================
     INPUT CHANGE
     ========================================================== */

  function handleInputChange(
    event: ChangeEvent<HTMLInputElement>,
  ): void {

    const file =
      event.target.files?.[0];


    if (!file) {

      return;
    }


    handleFileSelect(
      file,
    );
  }


  /* ==========================================================
     DRAG OVER
     ========================================================== */

  function handleDragOver(
    event: DragEvent<HTMLDivElement>,
  ): void {

    event.preventDefault();

    setIsDragging(
      true,
    );
  }


  /* ==========================================================
     DRAG LEAVE
     ========================================================== */

  function handleDragLeave(
    event: DragEvent<HTMLDivElement>,
  ): void {

    event.preventDefault();

    setIsDragging(
      false,
    );
  }


  /* ==========================================================
     DROP
     ========================================================== */

  function handleDrop(
    event: DragEvent<HTMLDivElement>,
  ): void {

    event.preventDefault();

    setIsDragging(
      false,
    );


    const file =
      event.dataTransfer.files?.[0];


    if (!file) {

      return;
    }


    handleFileSelect(
      file,
    );
  }


  /* ==========================================================
     OPEN FILE PICKER
     ========================================================== */

  function openFilePicker(): void {

    fileInputRef.current?.click();
  }


  /* ==========================================================
     CLEAR PROGRESS TIMER
     ========================================================== */

  function clearProgressTimer(): void {

    if (
      progressTimerRef.current !==
      null
    ) {

      window.clearInterval(
        progressTimerRef.current,
      );

      progressTimerRef.current =
        null;
    }
  }


  /* ==========================================================
     CLEAR SELECTION
     ========================================================== */

  function clearSelection(): void {

    clearProgressTimer();


    setSelectedFile(
      null,
    );

    setResult(
      null,
    );

    setError(
      null,
    );

    setUploadProgress(
      0,
    );


    if (
      fileInputRef.current
    ) {

      fileInputRef.current.value =
        "";
    }
  }


  /* ==========================================================
     UPLOAD
     ========================================================== */

  async function handleUpload(): Promise<void> {

    if (
      !selectedFile
    ) {

      setError(
        "Please select a CSV file first.",
      );

      return;
    }


    const validationError =
      validateFile(
        selectedFile,
      );


    if (
      validationError
    ) {

      setError(
        validationError,
      );

      return;
    }


    clearProgressTimer();


    try {

      setUploading(
        true,
      );

      setError(
        null,
      );

      setResult(
        null,
      );

      setUploadProgress(
        15,
      );


      progressTimerRef.current =
        window.setInterval(
          () => {

            setUploadProgress(
              (current) => {

                if (
                  current >=
                  85
                ) {

                  return current;
                }


                return Math.min(
                  current + 8,
                  85,
                );
              },
            );

          },
          180,
        );


      const data =
        await uploadCSV(
          selectedFile,
        );


      clearProgressTimer();


      setUploadProgress(
        100,
      );

      setResult(
        data,
      );

    } catch (
      err
    ) {

      clearProgressTimer();


      setUploadProgress(
        0,
      );


      setError(
        err instanceof Error
          ? err.message
          : "Upload failed.",
      );

    } finally {

      setUploading(
        false,
      );
    }
  }


  /* ==========================================================
     FORMAT FILE SIZE
     ========================================================== */

  function formatFileSize(
    bytes: number,
  ): string {

    if (
      bytes <
      1024
    ) {

      return `${bytes} B`;
    }


    if (
      bytes <
      1024 *
      1024
    ) {

      return `${(
        bytes / 1024
      ).toFixed(1)} KB`;
    }


    return `${(
      bytes /
      (1024 * 1024)
    ).toFixed(2)} MB`;
  }


  /* ==========================================================
     RENDER
     ========================================================== */

  return (

    <main className="relative min-h-screen overflow-hidden bg-[#07111f] text-white">


      {/* ======================================================
          FORENSIC BACKGROUND
          ====================================================== */}

      <AmbientBackground />


      {/* ======================================================
          MAIN CONTENT
          ====================================================== */}

      <section className="relative z-10 mx-auto max-w-5xl px-6 py-12">


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
          transition={{
            duration: 0.5,
          }}
        >

          <Link
            href="/"
            className="inline-flex items-center gap-2 text-sm text-white/40 transition hover:text-white"
          >

            <ArrowLeft
              className="h-4 w-4"
            />

            Back to overview

          </Link>


          <div className="mt-8">

            <div className="flex items-center gap-2 text-sm text-cyan-300/70">

              <FileSpreadsheet
                className="h-4 w-4"
              />

              Data ingestion

            </div>


            <h1 className="mt-3 text-4xl font-semibold tracking-tight sm:text-5xl">

              Bring your data

              <span className="block bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400 bg-clip-text text-transparent">

                into the investigation.

              </span>

            </h1>


            <p className="mt-4 max-w-2xl text-base leading-7 text-white/45">

              Upload a CSV dataset and let
              Journey Forensics validate,
              inspect and store it for analysis.

            </p>

          </div>

        </motion.div>


        {/* ====================================================
            UPLOAD CONTAINER
            ==================================================== */}

        <motion.section
          initial={{
            opacity: 0,
            y: 24,
          }}
          animate={{
            opacity: 1,
            y: 0,
          }}
          transition={{
            delay: 0.08,
            duration: 0.5,
          }}
          className="mt-10 overflow-hidden rounded-[2rem] border border-white/10 bg-[#101b2a]/80 shadow-[0_25px_80px_rgba(0,0,0,0.18)] backdrop-blur-2xl"
        >


          {/* ==================================================
              DROP ZONE
              ================================================== */}

          {!selectedFile &&
            !result && (

            <motion.div
              onDragOver={
                handleDragOver
              }
              onDragLeave={
                handleDragLeave
              }
              onDrop={
                handleDrop
              }
              animate={{
                scale:
                  isDragging
                    ? 1.008
                    : 1,
              }}
              className={`relative flex min-h-[390px] flex-col items-center justify-center overflow-hidden p-8 text-center transition ${
                isDragging
                  ? "bg-cyan-300/[0.06]"
                  : "bg-[#0b1624]/50"
              }`}
            >

              <input
                ref={
                  fileInputRef
                }
                type="file"
                accept=".csv,text/csv"
                onChange={
                  handleInputChange
                }
                className="hidden"
              />


              <div
                className={`absolute inset-5 rounded-[1.6rem] border border-dashed transition ${
                  isDragging
                    ? "border-cyan-300/60"
                    : "border-white/10"
                }`}
              />


              <motion.div
                animate={{
                  y:
                    isDragging
                      ? -8
                      : [
                          0,
                          -5,
                          0,
                        ],
                }}
                transition={
                  isDragging
                    ? {
                        duration: 0.2,
                      }
                    : {
                        duration: 3,
                        repeat:
                          Infinity,
                        ease:
                          "easeInOut",
                      }
                }
                className="relative z-10 flex h-20 w-20 items-center justify-center rounded-[1.7rem] border border-cyan-300/20 bg-cyan-300/10 shadow-[0_0_45px_rgba(103,232,249,0.07)]"
              >

                <CloudUpload
                  className="h-9 w-9 text-cyan-300"
                />

              </motion.div>


              <h2 className="relative z-10 mt-7 text-xl font-semibold">

                {isDragging
                  ? "Release to upload"
                  : "Drop your CSV here"}

              </h2>


              <p className="relative z-10 mt-2 text-sm text-white/35">

                or choose a file from your computer

              </p>


              <motion.button
                type="button"
                onClick={
                  openFilePicker
                }
                whileHover={{
                  scale: 1.03,
                }}
                whileTap={{
                  scale: 0.98,
                }}
                className="relative z-10 mt-7 inline-flex items-center gap-2 rounded-2xl bg-cyan-300 px-6 py-3.5 text-sm font-medium text-[#07111f] shadow-[0_10px_35px_rgba(103,232,249,0.12)]"
              >

                <UploadCloud
                  className="h-4 w-4"
                />

                Choose CSV file

              </motion.button>


              <div className="relative z-10 mt-7 flex flex-wrap justify-center gap-3">

                <span className="rounded-full border border-white/10 bg-white/[0.035] px-3 py-1.5 text-[10px] text-white/30">

                  CSV only

                </span>


                <span className="rounded-full border border-white/10 bg-white/[0.035] px-3 py-1.5 text-[10px] text-white/30">

                  Max 10 MB

                </span>


                <span className="rounded-full border border-white/10 bg-white/[0.035] px-3 py-1.5 text-[10px] text-white/30">

                  Server validated

                </span>

              </div>

            </motion.div>

          )}


          {/* ==================================================
              SELECTED FILE
              ================================================== */}

          {selectedFile &&
            !result && (

            <motion.div
              initial={{
                opacity: 0,
                y: 12,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              className="p-6 sm:p-8"
            >

              <div className="rounded-[1.6rem] border border-cyan-300/15 bg-cyan-300/[0.035] p-6">


                <div className="flex flex-col gap-5 sm:flex-row sm:items-center sm:justify-between">

                  <div className="flex min-w-0 items-center gap-4">

                    <div className="flex h-14 w-14 shrink-0 items-center justify-center rounded-2xl border border-cyan-300/10 bg-cyan-300/10">

                      <FileText
                        className="h-6 w-6 text-cyan-300"
                      />

                    </div>


                    <div className="min-w-0">

                      <p className="truncate font-medium text-white/90">
                        {selectedFile.name}
                      </p>


                      <p className="mt-1 text-xs text-white/35">

                        {formatFileSize(
                          selectedFile.size,
                        )}

                      </p>

                    </div>

                  </div>


                  {!uploading && (

                    <button
                      type="button"
                      onClick={
                        clearSelection
                      }
                      className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl border border-white/10 bg-white/5 text-white/40 transition hover:bg-white/10 hover:text-white"
                      aria-label="Remove selected file"
                    >

                      <X
                        className="h-4 w-4"
                      />

                    </button>

                  )}

                </div>


                {/* VALIDATION SUMMARY */}

                <div className="mt-6 grid gap-3 sm:grid-cols-3">

                  <ValidationCard
                    label="Format"
                    value="CSV validated"
                    icon={
                      <CheckCircle2
                        className="h-4 w-4"
                      />
                    }
                  />


                  <ValidationCard
                    label="File size"
                    value={
                      formatFileSize(
                        selectedFile.size,
                      )
                    }
                    icon={
                      <FileSpreadsheet
                        className="h-4 w-4"
                      />
                    }
                  />


                  <ValidationCard
                    label="Destination"
                    value="Analytics storage"
                    icon={
                      <ShieldCheck
                        className="h-4 w-4"
                      />
                    }
                  />

                </div>


                {/* PROGRESS */}

                {uploading && (

                  <motion.div
                    initial={{
                      opacity: 0,
                    }}
                    animate={{
                      opacity: 1,
                    }}
                    className="mt-7"
                  >

                    <div className="mb-2 flex items-center justify-between text-xs">

                      <span className="text-white/40">
                        Processing dataset
                      </span>


                      <span className="font-medium text-cyan-200">
                        {uploadProgress}%
                      </span>

                    </div>


                    <div className="h-2 overflow-hidden rounded-full bg-white/5">

                      <motion.div
                        className="h-full rounded-full bg-gradient-to-r from-cyan-300 via-blue-400 to-violet-400"
                        animate={{
                          width:
                            `${uploadProgress}%`,
                        }}
                        transition={{
                          duration: 0.2,
                        }}
                      />

                    </div>


                    <div className="mt-4 flex items-center justify-center gap-2 text-sm text-cyan-200/65">

                      <Loader2
                        className="h-4 w-4 animate-spin"
                      />

                      Validating and storing dataset...

                    </div>

                  </motion.div>

                )}


                {/* UPLOAD BUTTON */}

                {!uploading && (

                  <motion.button
                    type="button"
                    onClick={
                      () =>
                        void handleUpload()
                    }
                    whileHover={{
                      scale: 1.01,
                      boxShadow:
                        "0 12px 40px rgba(103,232,249,0.12)",
                    }}
                    whileTap={{
                      scale: 0.99,
                    }}
                    className="mt-7 flex w-full items-center justify-center gap-2 rounded-2xl bg-gradient-to-r from-cyan-300 to-sky-400 px-6 py-3.5 text-sm font-medium text-[#07111f]"
                  >

                    <CloudUpload
                      className="h-4 w-4"
                    />

                    Upload dataset

                  </motion.button>

                )}

              </div>

            </motion.div>

          )}


          {/* ==================================================
              SUCCESS
              ================================================== */}

          {result && (

            <motion.div
              initial={{
                opacity: 0,
                y: 15,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              transition={{
                duration: 0.45,
              }}
              className="p-6 sm:p-8"
            >

              <div className="rounded-[1.6rem] border border-emerald-300/15 bg-emerald-300/[0.035] p-7">


                <div className="flex flex-col items-center text-center">

                  <motion.div
                    initial={{
                      scale: 0,
                    }}
                    animate={{
                      scale: 1,
                    }}
                    transition={{
                      type: "spring",
                      stiffness: 220,
                      damping: 14,
                    }}
                    className="flex h-16 w-16 items-center justify-center rounded-3xl border border-emerald-300/20 bg-emerald-300/10"
                  >

                    <CheckCircle2
                      className="h-8 w-8 text-emerald-300"
                    />

                  </motion.div>


                  <h2 className="mt-5 text-2xl font-semibold">
                    Dataset uploaded successfully
                  </h2>


                  <p className="mt-2 max-w-xl text-sm leading-6 text-white/35">

                    Journey Forensics accepted the
                    dataset and returned its ingestion
                    metadata.

                  </p>

                </div>


                {/* RESULT METRICS */}

                <div className="mt-8 grid gap-3 sm:grid-cols-3">

                  <ResultCard
                    label="Rows"
                    value={
                      result.rows.toLocaleString()
                    }
                  />


                  <ResultCard
                    label="Columns"
                    value={
                      result.columns.toLocaleString()
                    }
                  />


                  <ResultCard
                    label="Status"
                    value={
                      result.status
                    }
                  />

                </div>


                {/* FILE */}

                <div className="mt-4 rounded-2xl border border-white/5 bg-black/10 p-5">

                  <div className="flex items-center gap-2 text-sm text-emerald-200/80">

                    <ShieldCheck
                      className="h-4 w-4"
                    />

                    Stored successfully

                  </div>


                  <p className="mt-3 text-xs text-white/30">
                    Original file
                  </p>


                  <p className="mt-1 truncate text-sm text-white/70">
                    {result.filename}
                  </p>


                  <p className="mt-4 text-xs text-white/30">
                    Stored filename
                  </p>


                  <p className="mt-1 break-all font-mono text-xs text-white/40">
                    {result.stored_filename}
                  </p>

                </div>


                {/* NEW UPLOAD */}

                <motion.button
                  type="button"
                  onClick={
                    clearSelection
                  }
                  whileHover={{
                    scale: 1.01,
                  }}
                  whileTap={{
                    scale: 0.99,
                  }}
                  className="mt-7 flex w-full items-center justify-center gap-2 rounded-2xl border border-white/10 bg-white/5 px-6 py-3.5 text-sm text-white/65 transition hover:bg-white/10 hover:text-white"
                >

                  <RefreshCw
                    className="h-4 w-4"
                  />

                  Upload another dataset

                </motion.button>

              </div>

            </motion.div>

          )}


          {/* ==================================================
              ERROR
              ================================================== */}

          {error && (

            <motion.div
              initial={{
                opacity: 0,
                y: 8,
              }}
              animate={{
                opacity: 1,
                y: 0,
              }}
              className="mx-6 mb-6 flex items-start gap-3 rounded-2xl border border-red-300/15 bg-red-300/[0.04] p-5 sm:mx-8"
            >

              <div className="flex h-9 w-9 shrink-0 items-center justify-center rounded-xl bg-red-300/10">

                <XCircle
                  className="h-4 w-4 text-red-300"
                />

              </div>


              <div className="min-w-0">

                <p className="text-sm font-medium text-red-200">
                  Upload could not be completed
                </p>


                <p className="mt-1 text-sm leading-6 text-white/40">
                  {error}
                </p>

              </div>

            </motion.div>

          )}

        </motion.section>


        {/* ====================================================
            TRUST CARDS
            ==================================================== */}

        <div className="mt-5 grid gap-4 md:grid-cols-3">

          <InfoCard
            icon={
              <ShieldCheck
                className="h-5 w-5 text-cyan-300"
              />
            }
            title="Validated ingestion"
            description="File type, size and basic upload constraints are checked before submission."
            delay={0}
          />


          <InfoCard
            icon={
              <FileSpreadsheet
                className="h-5 w-5 text-cyan-300"
              />
            }
            title="Dataset metadata"
            description="Successful ingestion returns row count, column count and storage metadata."
            delay={0.07}
          />


          <InfoCard
            icon={
              <Sparkles
                className="h-5 w-5 text-cyan-300"
              />
            }
            title="Ready for analysis"
            description="Accepted datasets become available to the broader forensic analytics workflow."
            delay={0.14}
          />

        </div>

      </section>


      {/* ======================================================
          FOOTER
          ====================================================== */}

      <footer className="relative z-10 border-t border-white/10 px-6 py-6">

        <div className="mx-auto flex max-w-5xl items-center justify-between text-xs text-white/25">

          <span>
            Journey Forensics
          </span>


          <span>
            Secure data ingestion
          </span>

        </div>

      </footer>

    </main>
  );
}


/* ============================================================
   VALIDATION CARD
   ============================================================ */

function ValidationCard({
  label,
  value,
  icon,
}: {
  label: string;
  value: string;
  icon: ReactNode;
}) {

  return (

    <div className="rounded-2xl border border-white/5 bg-black/10 p-4">

      <div className="flex items-center gap-2 text-[10px] text-white/30">

        {icon}

        {label}

      </div>


      <p className="mt-2 text-sm text-emerald-200">
        {value}
      </p>

    </div>
  );
}


/* ============================================================
   RESULT CARD
   ============================================================ */

function ResultCard({
  label,
  value,
}: {
  label: string;
  value: string;
}) {

  return (

    <div className="rounded-2xl border border-white/5 bg-black/10 p-5">

      <p className="text-[10px] uppercase tracking-wider text-white/30">
        {label}
      </p>


      <p className="mt-2 text-2xl font-semibold text-white/90">
        {value}
      </p>

    </div>
  );
}


/* ============================================================
   INFO CARD
   ============================================================ */

function InfoCard({
  icon,
  title,
  description,
  delay,
}: {
  icon: ReactNode;
  title: string;
  description: string;
  delay: number;
}) {

  return (

    <motion.div
      initial={{
        opacity: 0,
        y: 15,
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
        y: -3,
      }}
      className="rounded-3xl border border-white/10 bg-white/[0.03] p-5 backdrop-blur-xl"
    >

      <div className="flex h-10 w-10 items-center justify-center rounded-2xl bg-white/5">

        {icon}

      </div>


      <h3 className="mt-5 text-sm font-semibold">
        {title}
      </h3>


      <p className="mt-2 text-xs leading-6 text-white/35">
        {description}
      </p>

    </motion.div>
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

      <div className="absolute inset-0 bg-[radial-gradient(circle_at_8%_12%,rgba(34,211,238,0.065),transparent_27%),radial-gradient(circle_at_90%_30%,rgba(139,92,246,0.07),transparent_30%),radial-gradient(circle_at_52%_100%,rgba(59,130,246,0.04),transparent_28%)]" />


      <div
        className="absolute inset-0 opacity-[0.035]"
        style={{
          backgroundImage:
            "linear-gradient(rgba(103,232,249,.2) 1px, transparent 1px), linear-gradient(90deg, rgba(103,232,249,.2) 1px, transparent 1px)",
          backgroundSize:
            "72px 72px",
          maskImage:
            "radial-gradient(circle at center, black 12%, transparent 84%)",
          WebkitMaskImage:
            "radial-gradient(circle at center, black 12%, transparent 84%)",
        }}
      />


      <motion.div
        className="absolute -left-48 top-20 h-[32rem] w-[32rem] rounded-full bg-cyan-400/[0.055] blur-3xl"
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
            1.08,
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
        className="absolute right-[-160px] top-[30%] h-[36rem] w-[36rem] rounded-full bg-violet-500/[0.06] blur-3xl"
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
          duration: 17,
          repeat: Infinity,
          ease: "easeInOut",
        }}
      />


      <div className="absolute left-[6%] top-[36%] hidden h-60 w-60 lg:block">

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
          className="absolute inset-9 rounded-full border border-cyan-300/[0.035]"
          animate={{
            rotate: 360,
          }}
          transition={{
            duration: 30,
            repeat: Infinity,
            ease: "linear",
          }}
        />


        <span className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full bg-cyan-300/40 shadow-[0_0_18px_rgba(103,232,249,.4)]" />

      </div>


      <div className="absolute right-[7%] top-[22%] hidden h-72 w-72 lg:block">

        <motion.div
          className="absolute inset-0 rounded-full border border-violet-300/[0.055]"
          animate={{
            scale: [
              0.8,
              1.05,
              0.8,
            ],
            opacity: [
              0.12,
              0.42,
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
            duration: 34,
            repeat: Infinity,
            ease: "linear",
          }}
        />

      </div>


      <motion.div
        className="absolute inset-x-0 h-px bg-gradient-to-r from-transparent via-cyan-300/10 to-transparent"
        animate={{
          top: [
            "10%",
            "90%",
            "10%",
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
            "78%",
            "20%",
            "78%",
          ],
        }}
        transition={{
          duration: 25,
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
              `${7 + (index * 7.7) % 88}%`;

            const top =
              `${13 + (index * 14.2) % 75}%`;


            return (

              <motion.span
                key={
                  index
                }
                className="absolute h-1.5 w-1.5 rounded-full bg-cyan-200/20"
                style={{
                  left,
                  top,
                }}
                animate={{
                  y: [
                    0,
                    -9,
                    0,
                  ],
                  opacity: [
                    0.06,
                    0.4,
                    0.06,
                  ],
                  scale: [
                    0.8,
                    1.1,
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
                    0.32,
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


      <div className="absolute right-[5%] bottom-[18%] hidden h-8 w-8 opacity-15 lg:block">

        <span className="absolute left-1/2 top-0 h-full w-px -translate-x-1/2 bg-violet-300/50" />

        <span className="absolute left-0 top-1/2 h-px w-full -translate-y-1/2 bg-violet-300/50" />

        <span className="absolute left-1/2 top-1/2 h-1.5 w-1.5 -translate-x-1/2 -translate-y-1/2 rounded-full border border-violet-300/60" />

      </div>

    </div>
  );
}