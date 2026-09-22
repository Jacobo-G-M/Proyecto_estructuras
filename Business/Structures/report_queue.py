from ...Models.report import Report

class Report_Queue:
  # ------------------------
  #       CONSTRUCTOR
  # ------------------------
  def __init__(self):
    self.__current_reports: list[Report] = []

  # ------------------------
  #   GETTERS AND SETTERS
  # ------------------------
  @property
  def current_reports(self) -> list[Report]:
    return self.__current_reports

  @current_reports.setter
  def current_reports(self, value: list[Report]) -> None:
    self.__current_reports = value

  # ------------------------
  #         METHODS
  # ------------------------