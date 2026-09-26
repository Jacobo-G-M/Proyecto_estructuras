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
<<<<<<< HEAD
  
  # Method to enqueue a report
  def enqueue(self, report: Report) -> None:
    self.__current_reports.append(report)
  
  # Method to dequeue and get the first report added
  def dequeue(self) -> Report:
    return self.__current_reports.pop(0)
=======

    #verifies if the queue is empty or not -----
  def is_empty(self) -> bool:
    return len(self.__current_reports) == 0

    #method to get a shallow copy of the reports -----
  def view_all(self) -> list[Report]:
    return list(self.__current_reports)

    #method for insert a report on any position -----
  def add_in_position(self, report: Report, position: int) -> None:
    if type(report).__name__ != "Report":
      raise TypeError("Item must be an instance of Report.")
    
    if not isinstance(position, int) or position < 0 or position > len(self.__current_reports):
      raise IndexError("Position is out of bounds for the current queue.")
    
    self.__current_reports.insert(position, report)

  
>>>>>>> 2e5bd19d12ab082fb8f48be20abed8682690fb30
