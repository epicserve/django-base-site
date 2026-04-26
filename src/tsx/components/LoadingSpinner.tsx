import { Component } from "react";

interface Props {
  message?: string;
}

class LoadingSpinner extends Component<Props> {
  render() {
    const { message = "Loading..." } = this.props;
    return (
      <div className="d-flex justify-content-center align-items-center py-5">
        <div className="spinner-border text-primary me-3" role="status">
          <span className="visually-hidden">{message}</span>
        </div>
        <span className="text-muted">{message}</span>
      </div>
    );
  }
}

export default LoadingSpinner;
