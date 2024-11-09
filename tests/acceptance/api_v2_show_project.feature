Feature: show index page with some selected projects

  Scenario: show the projects with most downloads from yesterday
    Given today is 2018-05-30
    And the pyzn project with the following downloads
      | date       | version | downloads |
      | 2018-05-01 | 1.0     | 10        |
      | 2018-05-02 | 2.0     | 15        |
      | 2018-05-03 | 1.0     | 20        |
      | 2018-05-03 | 2.0     | 25        |
      | 2018-05-04 | 2.0     | 50        |
    When I send the GET request to /api/v2/projects/pyzn
    Then the response status code should be 200
    And the api response should be
    """
    {
      "id": "pyzn",
      "total_downloads": 120,
      "versions": ["1.0", "2.0"],
      "downloads": {
        "2018-05-01": {
          "1.0": 10
        },
        "2018-05-02": {
          "2.0": 15
        },
        "2018-05-03": {
          "1.0": 20,
          "2.0": 25
        },
        "2018-05-04": {
          "2.0": 50
        }
      }
    }
    """

  Scenario: do not show stats older than 4 months
    Given today is 2018-08-29
    And the pyzn project with the following downloads
      | date       | version | downloads |
      | 2018-04-29 | 1.0     | 10        |
      | 2018-04-30 | 1.0     | 10        |
      | 2018-05-01 | 1.0     | 10        |
      | 2018-05-02 | 2.0     | 15        |
      | 2018-05-03 | 1.0     | 20        |
      | 2018-05-03 | 2.0     | 25        |
      | 2018-05-04 | 2.0     | 50        |
    When I send the GET request to /api/v2/projects/pyzn
    Then the response status code should be 200
    And the api response should be
    """
    {
      "id": "pyzn",
      "total_downloads": 140,
      "versions": ["1.0", "2.0"],
      "downloads": {
        "2018-05-01": {
          "1.0": 10
        },
        "2018-05-02": {
          "2.0": 15
        },
        "2018-05-03": {
          "1.0": 20,
          "2.0": 25
        },
        "2018-05-04": {
          "2.0": 50
        }
      }
    }
    """

  Scenario: project name is case insensitive
    Given today is 2018-05-30
    And the pyzn project with the following downloads
      | date       | version | downloads |
      | 2018-05-01 | 1.0     | 10        |
    When I send the GET request to /api/v2/projects/Pyzn
    Then the response status code should be 200
    And the api response should be
    """
    {
      "id": "pyzn",
      "total_downloads": 10,
      "versions": ["1.0"],
      "downloads": {
        "2018-05-01": {
          "1.0": 10
        }
      }
    }
    """

  Scenario: order versions in natural order
    Given today is 2018-05-30
    And the pyzn project with the following downloads
      | date       | version | downloads |
      | 2018-05-01 | 2.1     | 10        |
      | 2018-05-01 | 2.9     | 10        |
      | 2018-05-01 | 2.10    | 10        |
    When I send the GET request to /api/v2/projects/Pyzn
    Then the response status code should be 200
    And the api response should be
    """
    {
      "id": "pyzn",
      "total_downloads": 30,
      "versions": ["2.1", "2.9", "2.10"],
      "downloads": {
        "2018-05-01": {
          "2.1": 10,
          "2.9": 10,
          "2.10": 10
        }
      }
    }
    """

  Scenario: show 404 when project not found
    When I send the GET request to /api/v2/projects/pyzn
    Then the response status code should be 404
    And the api response should be
    """
      {
        "error": 404,
        "message": "Project with name pyzn does not exist"
      }
    """