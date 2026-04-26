import { StrictMode } from "react";
import { createRoot } from "react-dom/client";
import DashboardPage from "./pages/DashboardPage";

const container = document.getElementById("budget-app");
if (container) {
  const budgetPk = parseInt(container.dataset.budgetPk ?? "0", 10);
  const initialMonth = container.dataset.month || undefined;

  createRoot(container).render(
    <StrictMode>
      <DashboardPage budgetPk={budgetPk} initialMonth={initialMonth} />
    </StrictMode>
  );
}
