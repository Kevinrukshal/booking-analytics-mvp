import React, { lazy, Suspense } from "react";
import ReactDOM from "react-dom/client";
import { createBrowserRouter, RouterProvider } from "react-router-dom";
import { AppLayout } from "./components/layout/AppLayout";
import "./index.css";
import { LoadingState } from "./components/ui/PageStates";

const Overview = lazy(() => import("./pages/Overview").then((module) => ({ default: module.Overview })));
const Bookings = lazy(() => import("./pages/Bookings").then((module) => ({ default: module.Bookings })));
const BookingDetail = lazy(() => import("./pages/BookingDetail").then((module) => ({ default: module.BookingDetail })));
const Agents = lazy(() => import("./pages/Agents").then((module) => ({ default: module.Agents })));
const AgentDetail = lazy(() => import("./pages/AgentDetail").then((module) => ({ default: module.AgentDetail })));
const Errors = lazy(() => import("./pages/Errors").then((module) => ({ default: module.Errors })));
const UploadPage = lazy(() => import("./pages/Upload").then((module) => ({ default: module.UploadPage })));

const deferred = (element: React.ReactNode) => <Suspense fallback={<LoadingState rows={5} />}>{element}</Suspense>;

const router = createBrowserRouter([{ path: "/", element: <AppLayout />, children: [
  { index: true, element: deferred(<Overview />) },
  { path: "bookings", element: deferred(<Bookings />) },
  { path: "bookings/:reference", element: deferred(<BookingDetail />) },
  { path: "agents", element: deferred(<Agents />) },
  { path: "agents/:agent", element: deferred(<AgentDetail />) },
  { path: "errors", element: deferred(<Errors />) },
  { path: "upload", element: deferred(<UploadPage />) },
]}]);

ReactDOM.createRoot(document.getElementById("root")!).render(<React.StrictMode><RouterProvider router={router} /></React.StrictMode>);
