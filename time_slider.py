from superqt import QRangeSlider

class TimeSlider(QRangeSlider):

    def __init__(self, _IntMixin):
        super().__init__(_IntMixin)

        self.positions = []
        for i in range(0, 60, 5):
            self.positions.append((i, f'{i} минут'))

        for i in range(60, 180, 15):
            self.positions.append((i, self.get_time_description(i)))

        for i in range(180, 480, 30):
            self.positions.append((i, self.get_time_description(i)))

        for i in range(480, 2400, 60):
            self.positions.append((i, self.get_time_description(i)))

        self.positions.append((9999999999999999999, 'Максимум'))

        self.setRange(0, len(self.positions))
        self.setValue((0, len(self.positions)))

    def get_time_description(self, min_count):
        hours = min_count // 60
        minutes = min_count % 60
        hours_str = 'часов'
        if hours == 1 or (hours > 20 and hours % 10 == 1):
            hours_str = 'час'
        elif 1 < hours < 5 or (hours > 20 and 1 < hours % 10 < 5):
            hours_str = 'часа'

        pos_description = f'{hours} {hours_str}'
        if minutes:
            pos_description = f'{pos_description} {minutes} минут'
        return pos_description

    def get_description(self, position):
        pos = int(position)
        pos = pos if pos < len(self.positions) else len(self.positions) - 1
        return self.positions[pos][1]

    def get_value(self, position):
        pos = int(position)
        pos = pos if pos < len(self.positions) else len(self.positions) - 1
        return self.positions[pos][0]

    def default_value(self, position):
        return int(position) == 0 or int(position) == len(self.positions)
