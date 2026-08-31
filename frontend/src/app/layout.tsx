import type {
  Metadata,
} from "next";

import "./globals.css";

import AppNavigation from "@/components/app-navigation";

import AppBootLoader from "@/components/app-boot-loader";


export const metadata: Metadata = {

  title:
    "Journey Forensics",

  description:
    "Forensic intelligence platform for customer journeys, behavioral analytics, payment friction and investigations.",

  keywords: [
    "Journey Forensics",
    "customer intelligence",
    "journey analytics",
    "forensic analytics",
    "payment friction",
    "data intelligence",
  ],

};


export default function RootLayout({
  children,
}: Readonly<{
  children: React.ReactNode;
}>) {

  return (

    <html lang="en">

      <body>

        {/* ================================================
            PREMIUM APP BOOT
            ================================================ */}

        <AppBootLoader />


        {/* ================================================
            GLOBAL NAVIGATION
            ================================================ */}

        <AppNavigation />


        {/* ================================================
            APPLICATION
            ================================================ */}

        <div className="app-content">

          {children}

        </div>

      </body>

    </html>

  );
}