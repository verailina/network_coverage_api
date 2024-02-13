import pandas as pd
from matplotlib import pyplot as plt

from network_coverage_api.api.schemas import Operator
from network_coverage_api.utils import get_data_path


class MapData:
    def __init__(self):
        self.operator_data = dict()

    def get_operator_data(self, operator: Operator) -> pd.DataFrame:
        if operator not in self.operator_data:
            self.operator_data[operator] = self.load_datasource(operator)

        return self.operator_data[operator]

    @staticmethod
    def load_datasource(operator: Operator) -> pd.DataFrame:
        data_path = get_data_path(f"{operator.name}_datasource.csv")
        if data_path.exists():
            df = pd.read_csv(data_path, index_col=0)
            df.index = df.index.astype(int)
        else:
            raise FileNotFoundError(f"Could not find {data_path}")
        return df

    def visualize_clusters(self, operator: Operator) -> None:
        df = self.get_operator_data(operator)
        df = df.reset_index()
        df.plot.scatter(x="longitude", y="latitude", c="cluster")
        plt.show()


if __name__ == "__main__":
    map_data = MapData()
    map_data.visualize_clusters(Operator.Free)
