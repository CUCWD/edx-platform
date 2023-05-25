import React, { Component } from 'react';
import ReactDOM from 'react-dom';

import $ from 'jquery';

// Due to an issue with importing modal from paragon, 
// a modal has been made from scratch instead of importing a new one
// import { Button, Modal } from '@edx/paragon';


class ModalView extends Component {

  constructor(props) {
    super(props);
    this.state = {
      show: true,
      tos_html: '',
      has_user_agreed_to_latest_tos: true,
      tos_isChecked: false,
    };
    this.showModal = this.showModal.bind(this);
    this.hideModal = this.hideModal.bind(this);
    this.checkboxClicked = this.checkboxClicked.bind(this);
    this.isCheckboxClicked = this.isCheckboxClicked.bind(this);
    this.retrievePage();
  }

  checkboxClicked() {
    var isChecked = this.state.tos_isChecked;
    this.setState({ tos_isChecked: !isChecked });
  }


  isCheckboxClicked() {
    return !this.state.tos_isChecked;
  }

  retrievePage() {
    $.get('/termsofservice/v1/current_tos/')
      .then(data => {
        this.setState({
          tos_html: data.tos_html,
          has_user_agreed_to_latest_tos: data.has_user_agreed_to_latest_tos
        });
      });
  }

  showModal() {
    console.log(this.state);
    this.setState({ show: true });
  }


  hideModal() {

    var CSRFT = 'csrftoken';

    var csrftoken = null;
    if (document.cookie && document.cookie !== '') {
        var cookies = document.cookie.split(';');
        for (var i = 0; i < cookies.length; i++) {
            var cookie = cookies[i].trim();
            // Does this cookie string begin with the name we want?
            if (cookie.substring(0, CSRFT.length + 1) === (CSRFT + '=')) {
                csrftoken = decodeURIComponent(cookie.substring(CSRFT.length + 1));
                break;
            }
        }
    }

    fetch('/termsofservice/v1/current_tos/', {
      method: 'POST',
      mode: 'cors',
      headers: {
        'Content-Type': 'application/json',
        'X-CSRFToken': csrftoken
      },
      body: JSON.stringify({
        has_user_agreed: true
      })

    })
    this.setState({ show: false });
  }

  render() {

    if (this.state.has_user_agreed_to_latest_tos) {
      return (<div></div>)
    }
    else {
      return (

        <main>
          <Modal show={this.state.show} handleClose={this.hideModal} >
            <h2 className="mt-3 text-center">Terms of Service Agreement</h2>
            <p className="text-center">EducateWorkforce has updated its terms of service. Please read the following terms and agree in order to continue use of the platform.</p>

            <div className="modal-body border border-dark rounded m-3">
              <div className="scrollable_tos_style"  dangerouslySetInnerHTML={{ __html: (this.state.tos_html) }}></div>
            </div>

            <div className="modal-footer d-inline text-center">
              <form>
                <div className="form-check d-flex justify-content-center flex-nowrap">
                  <input className="form-check-input" type="checkbox" value="" onChange={this.checkboxClicked} id="agree-to-tos"></input>
                  <label className="form-check-label m-3" htmlFor="agree-to-tos">
                    I agree to the EducateWorkforce Terms of Service
                  </label>
                </div>
                <button type="submit" disabled={this.isCheckboxClicked()} onClick={this.hideModal} className="submit-btn btn btn-primary">Continue to Dashboard</button>
              </form>
            </div>
          </Modal>
        </main>
      )
    }
  }
}


const Modal = ({ show, children }) => {
  const showHideModal = show ? "modal-tos display-block" : "modal-tos display-none";

  return (
    <div className={showHideModal}>
      <section className="modal-main-tos">
        {children}
      </section>
    </div>
  );
};

export default class TOSModalView {
  constructor() {
    ReactDOM.render(
      <ModalView />,
      document.getElementById("tos-modal"),
    );
  }
}

export { TOSModalView, ModalView }