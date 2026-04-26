import { Component, createRef } from "react";
import type { Category, PaymentMethod, Transaction, TransactionLine } from "../types";

interface Props {
  categories: Category[];
  paymentMethods: PaymentMethod[];
  budgetPk: number;
  onSave: (data: Partial<Transaction>) => Promise<void>;
  transaction?: Transaction | null;
  onClose: () => void;
}

interface LineState {
  category: string;
  amount: string;
  description: string;
}

interface State {
  description: string;
  due_date: string;
  paid_date: string;
  is_paid: boolean;
  notes: string;
  payment_method: string;
  lines: LineState[];
  saving: boolean;
  errors: Record<string, string[]>;
}

class TransactionModal extends Component<Props, State> {
  private modalRef = createRef<HTMLDivElement>();

  constructor(props: Props) {
    super(props);
    this.state = this.buildInitialState(props.transaction);
  }

  buildInitialState(transaction?: Transaction | null): State {
    if (transaction) {
      return {
        description: transaction.description,
        due_date: transaction.due_date,
        paid_date: transaction.paid_date ?? "",
        is_paid: transaction.is_paid,
        notes: transaction.notes,
        payment_method: transaction.payment_method ? String(transaction.payment_method) : "",
        lines: transaction.lines.map((l) => ({
          category: String(l.category),
          amount: l.amount,
          description: l.description,
        })),
        saving: false,
        errors: {},
      };
    }
    return {
      description: "",
      due_date: new Date().toISOString().split("T")[0],
      paid_date: "",
      is_paid: false,
      notes: "",
      payment_method: "",
      lines: [{ category: "", amount: "", description: "" }],
      saving: false,
      errors: {},
    };
  }

  componentDidUpdate(prevProps: Props) {
    if (prevProps.transaction !== this.props.transaction) {
      this.setState(this.buildInitialState(this.props.transaction));
    }
  }

  handleLineChange(index: number, field: keyof LineState, value: string) {
    const lines = [...this.state.lines];
    lines[index] = { ...lines[index], [field]: value };
    this.setState({ lines });
  }

  addLine() {
    this.setState((prev) => ({
      lines: [...prev.lines, { category: "", amount: "", description: "" }],
    }));
  }

  removeLine(index: number) {
    this.setState((prev) => ({
      lines: prev.lines.filter((_, i) => i !== index),
    }));
  }

  async handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const { description, due_date, paid_date, is_paid, notes, payment_method, lines } = this.state;

    const payload: Partial<Transaction> = {
      description,
      due_date,
      paid_date: paid_date || null,
      is_paid,
      notes,
      payment_method: payment_method ? parseInt(payment_method, 10) : null,
      lines: lines.map((l) => ({
        category: parseInt(l.category, 10),
        amount: l.amount,
        description: l.description,
      })) as TransactionLine[],
    };

    this.setState({ saving: true, errors: {} });
    try {
      await this.props.onSave(payload);
      this.setState(this.buildInitialState());
      this.props.onClose();
    } catch (err: unknown) {
      this.setState({ errors: err as Record<string, string[]>, saving: false });
    }
  }

  render() {
    const { categories, paymentMethods, transaction, onClose } = this.props;
    const { description, due_date, paid_date, is_paid, notes, payment_method, lines, saving, errors } = this.state;
    const isEdit = Boolean(transaction);

    return (
      <div className="modal fade show d-block" tabIndex={-1} role="dialog" ref={this.modalRef}>
        <div className="modal-dialog modal-lg" role="document">
          <div className="modal-content">
            <form onSubmit={(e) => { void this.handleSubmit(e); }}>
              <div className="modal-header">
                <h5 className="modal-title">{isEdit ? "Edit Transaction" : "Add Transaction"}</h5>
                <button type="button" className="btn-close" onClick={onClose} aria-label="Close" />
              </div>
              <div className="modal-body">
                {errors.non_field_errors && (
                  <div className="alert alert-danger">{errors.non_field_errors.join(" ")}</div>
                )}

                <div className="mb-3">
                  <label className="form-label">Description</label>
                  <input
                    type="text"
                    className={`form-control ${errors.description ? "is-invalid" : ""}`}
                    value={description}
                    onChange={(e) => { this.setState({ description: e.target.value }); }}
                    required
                  />
                  {errors.description && <div className="invalid-feedback">{errors.description.join(" ")}</div>}
                </div>

                <div className="row">
                  <div className="col-md-6 mb-3">
                    <label className="form-label">Due Date</label>
                    <input
                      type="date"
                      className={`form-control ${errors.due_date ? "is-invalid" : ""}`}
                      value={due_date}
                      onChange={(e) => { this.setState({ due_date: e.target.value }); }}
                      required
                    />
                    {errors.due_date && <div className="invalid-feedback">{errors.due_date.join(" ")}</div>}
                  </div>
                  <div className="col-md-6 mb-3">
                    <label className="form-label">Paid Date</label>
                    <input
                      type="date"
                      className="form-control"
                      value={paid_date}
                      onChange={(e) => { this.setState({ paid_date: e.target.value }); }}
                    />
                  </div>
                </div>

                <div className="mb-3 form-check">
                  <input
                    type="checkbox"
                    className="form-check-input"
                    id="modal-is-paid"
                    checked={is_paid}
                    onChange={(e) => { this.setState({ is_paid: e.target.checked }); }}
                  />
                  <label className="form-check-label" htmlFor="modal-is-paid">Mark as Paid</label>
                </div>

                <div className="row">
                  <div className="col-md-6 mb-3">
                    <label className="form-label">Payment Method</label>
                    <select
                      className="form-select"
                      value={payment_method}
                      onChange={(e) => { this.setState({ payment_method: e.target.value }); }}
                    >
                      <option value="">— None —</option>
                      {paymentMethods.filter((m) => m.is_active).map((m) => (
                        <option key={m.id} value={m.id}>
                          {m.name}{m.last_four ? ` ···${m.last_four}` : ""}
                        </option>
                      ))}
                    </select>
                  </div>
                </div>

                <div className="mb-3">
                  <label className="form-label">Notes</label>
                  <textarea
                    className="form-control"
                    rows={2}
                    value={notes}
                    onChange={(e) => { this.setState({ notes: e.target.value }); }}
                  />
                </div>

                <hr />
                <h6>Line Items</h6>
                {errors.lines && (
                  <div className="alert alert-danger">{(errors.lines as unknown as string[]).join(" ")}</div>
                )}
                {lines.map((line, idx) => (
                  <div key={idx} className="row g-2 mb-2 align-items-end">
                    <div className="col-md-5">
                      <label className="form-label small">Category</label>
                      <select
                        className="form-select"
                        value={line.category}
                        onChange={(e) => { this.handleLineChange(idx, "category", e.target.value); }}
                        required
                      >
                        <option value="">-- Select --</option>
                        <optgroup label="Income">
                          {categories
                            .filter((c) => c.category_type === "income")
                            .map((c) => (
                              <option key={c.id} value={c.id}>{c.name}</option>
                            ))}
                        </optgroup>
                        <optgroup label="Expense">
                          {categories
                            .filter((c) => c.category_type === "expense")
                            .map((c) => (
                              <option key={c.id} value={c.id}>{c.name}</option>
                            ))}
                        </optgroup>
                      </select>
                    </div>
                    <div className="col-md-3">
                      <label className="form-label small">Amount</label>
                      <input
                        type="number"
                        step="0.01"
                        min="0.01"
                        className="form-control"
                        value={line.amount}
                        onChange={(e) => { this.handleLineChange(idx, "amount", e.target.value); }}
                        required
                      />
                    </div>
                    <div className="col-md-3">
                      <label className="form-label small">Note</label>
                      <input
                        type="text"
                        className="form-control"
                        value={line.description}
                        onChange={(e) => { this.handleLineChange(idx, "description", e.target.value); }}
                      />
                    </div>
                    <div className="col-md-1">
                      {lines.length > 1 && (
                        <button
                          type="button"
                          className="btn btn-outline-danger btn-sm"
                          onClick={() => { this.removeLine(idx); }}
                        >
                          &times;
                        </button>
                      )}
                    </div>
                  </div>
                ))}
                <button type="button" className="btn btn-sm btn-outline-secondary mt-1" onClick={() => { this.addLine(); }}>
                  + Add Line
                </button>
              </div>
              <div className="modal-footer">
                <button type="button" className="btn btn-secondary" onClick={onClose}>Cancel</button>
                <button type="submit" className="btn btn-primary" disabled={saving}>
                  {saving ? "Saving…" : "Save Transaction"}
                </button>
              </div>
            </form>
          </div>
        </div>
      </div>
    );
  }
}

export default TransactionModal;
