import React from "react";
import './DisqualifiedPage.css'

function DisqualifiedPage() {
  return (
    <div className="disqualified-container">
      <h1 className="disqualified-title">Disqualified</h1>
      <p className="disqualified-message">
        You have been disqualified as the number of suspected malpractices
        detected has exceeded the threshold.
      </p>
    </div>
  );
}

export default DisqualifiedPage;
